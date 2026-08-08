"""HTTP access to the OpenAlex API."""

import asyncio
import logging
import os
import random
from importlib.metadata import PackageNotFoundError, version
from typing import Any
from urllib.parse import quote

import httpx

from pub_analyzer.internal.limiter import RateLimiter
from pub_analyzer.internal.openalex.parsing import get_valid_works, validate_works
from pub_analyzer.models.source import Source
from pub_analyzer.models.work import Work

logger = logging.getLogger(__name__)

REQUEST_RATE_PER_SECOND = 20
"""The OpenAlex API allows a maximum of 100 requests per second. We stay well below that,
both to leave the service room and because the daily credit allowance runs out long
before the per-second limit is reached."""

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
"""Per-request timeout. Requests that expire are retried, so this stays well below the
time a user is willing to wait on a frozen screen."""

MAX_ATTEMPTS = 4
"""How many times a single request is attempted before giving up."""

INITIAL_BACKOFF_SECONDS = 1.0
"""Delay before the first retry. Doubles on every further attempt."""

MAX_BACKOFF_SECONDS = 30.0
"""Ceiling for the delay between retries, including server requested ones."""

RETRYABLE_STATUS_CODES = frozenset(
    {
        httpx.codes.REQUEST_TIMEOUT,
        httpx.codes.TOO_EARLY,
        httpx.codes.TOO_MANY_REQUESTS,
        httpx.codes.INTERNAL_SERVER_ERROR,
        httpx.codes.BAD_GATEWAY,
        httpx.codes.SERVICE_UNAVAILABLE,
        httpx.codes.GATEWAY_TIMEOUT,
    }
)
"""Statuses worth attempting again. Every other error status fails immediately."""

AUTHENTICATION_STATUS_CODES = frozenset(
    {
        httpx.codes.UNAUTHORIZED,
        httpx.codes.FORBIDDEN,
        httpx.codes.CONFLICT,
        httpx.codes.TOO_MANY_REQUESTS,
    }
)
"""Statuses OpenAlex answers with when a key is missing, rejected, or out of credits."""

API_KEY_ENV_VAR = "PUB_ANALYZER_API_KEY"
"""Environment variable holding the OpenAlex API key."""

API_KEY_PARAM = "api_key"
"""Query parameter carrying the API key, the only authentication OpenAlex accepts."""

API_KEY_SETTINGS_URL = "https://openalex.org/settings/api"
"""Where a user obtains a key."""

PROJECT_URL = "https://pub-analyzer.com"


def get_api_key() -> str | None:
    """Read the OpenAlex API key from the environment.

    Returns:
        The API key, or `None` when the user has not configured one.

    Info:
        OpenAlex has required a key on every call since February 2026. Without one a
        handful of requests succeed before the API starts refusing them, which is not
        enough to build even a small report.
    """
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()

    return api_key or None


def redact_api_key(url: object) -> str:
    """Remove the API key from a URL so it is safe to show or log.

    Args:
        url: URL, or anything rendering as one.

    Returns:
        The URL with the API key replaced by a placeholder.

    Example:
        ```python
        redact_api_key("https://api.openalex.org/works?api_key=secret")
        # 'https://api.openalex.org/works?api_key=REDACTED'
        ```
    """
    parsed = httpx.URL(str(url))
    if API_KEY_PARAM not in parsed.params:
        return str(parsed)

    return str(parsed.copy_set_param(API_KEY_PARAM, "REDACTED"))


def build_user_agent() -> str:
    """Build the User-Agent identifying pub-analyzer to OpenAlex.

    Returns:
        User-Agent header value.
    """
    try:
        package_version = version("pub-analyzer")
    except PackageNotFoundError:  # pragma: no cover - only when running from a source tree
        package_version = "unknown"

    return f"pub-analyzer/{package_version} (+{PROJECT_URL})"


def create_client() -> httpx.AsyncClient:
    """Create the HTTPX client used for every request of a report.

    Returns:
        Asynchronous client, configured with a timeout and an identifying User-Agent.
    """
    return httpx.AsyncClient(http2=True, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": build_user_agent()})


def _parse_retry_after(response: httpx.Response) -> float | None:
    """Read the delay a server asked us to wait for.

    Args:
        response: Response carrying an optional `Retry-After` header.

    Returns:
        Seconds to wait, or `None` when the header is missing or not a plain number.
    """
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return None

    try:
        return float(retry_after)
    except ValueError:
        # The header also allows an HTTP date, which we do not attempt to parse.
        return None


class OpenAlexClient:
    """Reads entities from the OpenAlex API, retrying transient failures.

    Wraps an HTTPX client with the rate limiting, pagination and retry behaviour every
    OpenAlex call in a report needs.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        limiter: RateLimiter | None = None,
        max_attempts: int = MAX_ATTEMPTS,
        initial_backoff: float = INITIAL_BACKOFF_SECONDS,
        api_key: str | None = None,
    ) -> None:
        self.client = client
        self.limiter = limiter if limiter is not None else RateLimiter(rate=REQUEST_RATE_PER_SECOND, per_second=1.0)
        self.max_attempts = max_attempts
        self.initial_backoff = initial_backoff
        self.api_key = api_key if api_key is not None else get_api_key()

    def _authenticated_url(self, url: str) -> str:
        """Attach the API key to a URL.

        Args:
            url: URL to authenticate.

        Returns:
            The URL carrying the API key, or unchanged when no key is configured.

        Danger:
            The result holds a secret. Log the original URL, never this one.
        """
        if not self.api_key:
            return url

        separator = "&" if "?" in url else "?"

        return f"{url}{separator}{API_KEY_PARAM}={quote(self.api_key, safe='')}"

    def _backoff_delay(self, attempt: int, retry_after: float | None) -> float:
        """Compute how long to wait before the next attempt.

        Args:
            attempt: Number of the attempt that just failed, starting at 1.
            retry_after: Delay requested by the server, if any.

        Returns:
            Seconds to sleep.
        """
        if retry_after is not None:
            return min(retry_after, MAX_BACKOFF_SECONDS)

        delay = min(self.initial_backoff * 2 ** (attempt - 1), MAX_BACKOFF_SECONDS)

        # Jitter keeps concurrent requests from retrying in lockstep.
        return delay * (0.5 + random.random() / 2)

    async def get_json(self, url: str) -> dict[str, Any]:
        """Get the JSON body of a URL, retrying transient failures.

        Args:
            url: URL to request.

        Returns:
            Decoded JSON body.

        Raises:
            httpx.HTTPStatusError: The API answered with an error status, either one we do
                not retry or one that kept failing until attempts ran out.
            httpx.TransportError: The request kept failing to reach the API.
        """
        last_error: Exception

        # Carries the API key, so it is passed to HTTPX but never to the log.
        request_url = self._authenticated_url(url)

        for attempt in range(1, self.max_attempts + 1):
            retry_after: float | None = None

            await self.limiter.acquire()
            try:
                response = await self.client.get(url=request_url, follow_redirects=True)
            except httpx.TransportError as exc:
                last_error = exc
                logger.warning(f"Request to {url} failed [{attempt}/{self.max_attempts}]: {exc}")
            else:
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    # Raises for any other error status, so callers fail fast on a 404.
                    response.raise_for_status()
                    json_response: dict[str, Any] = response.json()
                    return json_response

                retry_after = _parse_retry_after(response)
                last_error = httpx.HTTPStatusError(
                    f"Retryable status {response.status_code} for url: {url}", request=response.request, response=response
                )
                logger.warning(f"Request to {url} returned {response.status_code} [{attempt}/{self.max_attempts}]")

            if attempt < self.max_attempts:
                await asyncio.sleep(self._backoff_delay(attempt, retry_after))

        raise last_error

    async def get_works(self, url: str) -> list[Work]:
        """Get every work matching a URL, walking all result pages.

        Args:
            url: URL of works with all filters and sorting applied.

        Returns:
            List of Works Models.

        Raises:
            httpx.HTTPStatusError: A response from the OpenAlex API had an error status.
            httpx.TransportError: A request kept failing to reach the API.

        Info:
            Paging uses a cursor rather than page numbers, because page numbers cannot
            reach past the first 10.000 results.
        """
        works_data: list[dict[str, Any]] = []

        cursor: str | None = "*"
        seen_cursors: set[str] = set()

        # A cursor we already followed means the API stopped advancing; bail out rather
        # than page forever.
        while cursor and cursor not in seen_cursors:
            seen_cursors.add(cursor)

            json_response = await self.get_json(f"{url}&cursor={cursor}")
            works_data.extend(get_valid_works(json_response["results"]))
            cursor = json_response["meta"].get("next_cursor")

        return validate_works(works_data)

    async def get_source(self, url: str) -> Source:
        """Get a single source.

        Args:
            url: URL of the source.

        Returns:
            Source Model.

        Raises:
            httpx.HTTPStatusError: A response from the OpenAlex API had an error status.
            httpx.TransportError: A request kept failing to reach the API.
        """
        json_response = await self.get_json(url)

        homepage_url = json_response.get("homepage_url")
        if isinstance(homepage_url, str) and not homepage_url.startswith(("http", "https")):
            json_response["homepage_url"] = None
            logger.warning(f"Discarted source homepage url: {url}")

        return Source(**json_response)
