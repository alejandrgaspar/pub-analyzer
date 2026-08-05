"""Test the OpenAlex client from pub_analyzer/internal/openalex/client.py."""

from typing import Any

import httpx
import pytest
import respx

from pub_analyzer.internal.limiter import RateLimiter
from pub_analyzer.internal.openalex import client as openalex_client
from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR, OpenAlexClient
from tests.data.source import SOURCE
from tests.data.work import WORK

WORKS_URL = "https://api.openalex.org/works?filter=author.id:A0&sort=publication_date&per-page=200"
SOURCE_URL = "https://api.openalex.org/sources/S137773608"


def build_client(max_attempts: int = 4, api_key: str | None = None) -> OpenAlexClient:
    """Build a client that never sleeps between retries."""
    return OpenAlexClient(
        client=httpx.AsyncClient(),
        limiter=RateLimiter(rate=100, per_second=1.0),
        max_attempts=max_attempts,
        initial_backoff=0.0,
        api_key=api_key,
    )


def works_page(results: list[dict[str, Any]], next_cursor: str | None) -> dict[str, Any]:
    """Build a cursor paginated works payload."""
    return {"meta": {"count": len(results), "per_page": 100, "next_cursor": next_cursor}, "results": results}


# --- Authentication -------------------------------------------------------------------


def test_get_api_key_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_api_key function."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "secret-key")

    assert openalex_client.get_api_key() == "secret-key"


@pytest.mark.parametrize("value", ["", "   "], ids=["empty", "blank"])
def test_get_api_key_ignores_blank_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """A blank variable counts as no key at all."""
    monkeypatch.setenv(API_KEY_ENV_VAR, value)

    assert openalex_client.get_api_key() is None


def test_get_api_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """No variable, no key."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    assert openalex_client.get_api_key() is None


@pytest.mark.asyncio
async def test_requests_carry_the_api_key() -> None:
    """The key travels as a query parameter, the only form OpenAlex accepts."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.OK, json={"ok": True}))

        await build_client(api_key="secret-key").get_json(SOURCE_URL)

    assert route.calls[0].request.url.params["api_key"] == "secret-key"


@pytest.mark.asyncio
async def test_requests_without_a_key_are_unauthenticated() -> None:
    """No key configured means no parameter, rather than an empty one."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.OK, json={"ok": True}))

        await build_client(api_key=None).get_json(SOURCE_URL)

    assert "api_key" not in route.calls[0].request.url.params


@pytest.mark.asyncio
async def test_api_key_is_appended_to_urls_that_already_have_parameters() -> None:
    """The key joins an existing query string instead of starting a new one."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=WORKS_URL).mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=works_page([], next_cursor=None))
        )

        await build_client(api_key="secret-key").get_works(WORKS_URL)

    params = route.calls[0].request.url.params
    assert params["api_key"] == "secret-key"
    assert params["filter"] == "author.id:A0"
    assert params["cursor"] == "*"


def test_api_key_is_url_encoded() -> None:
    """A key containing reserved characters does not corrupt the query string."""
    authenticated = build_client(api_key="a&b=c d")._authenticated_url("https://api.openalex.org/works?filter=x")

    assert authenticated == "https://api.openalex.org/works?filter=x&api_key=a%26b%3Dc%20d"


class _RecordingLog:
    """Stand-in for the Textual logger, capturing what would be written."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def warning(self, message: object) -> None:
        """Record a warning."""
        self.messages.append(str(message))

    def info(self, message: object) -> None:
        """Record an informational message."""
        self.messages.append(str(message))


@pytest.mark.asyncio
async def test_api_key_never_reaches_the_log(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failures log the plain URL, never the authenticated one."""
    recording_log = _RecordingLog()
    monkeypatch.setattr(openalex_client, "log", recording_log)
    logged = recording_log.messages

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith=SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.SERVICE_UNAVAILABLE))

        with pytest.raises(httpx.HTTPStatusError):
            await build_client(max_attempts=2, api_key="secret-key").get_json(SOURCE_URL)

    assert logged, "expected the failures to be logged"
    assert not any("secret-key" in message for message in logged)


@pytest.mark.parametrize(
    ["url", "expected"],
    [
        pytest.param(
            "https://api.openalex.org/works?filter=x&api_key=secret",
            "https://api.openalex.org/works?filter=x&api_key=REDACTED",
            id="key-replaced",
        ),
        pytest.param(
            # Rebuilding the query percent encodes the other parameters. The result is only
            # ever shown or logged, so an encoded `*` is fine.
            "https://api.openalex.org/works?api_key=secret&cursor=*",
            "https://api.openalex.org/works?api_key=REDACTED&cursor=%2A",
            id="key-among-other-params",
        ),
        pytest.param(
            "https://api.openalex.org/works?filter=x",
            "https://api.openalex.org/works?filter=x",
            id="no-key-untouched",
        ),
    ],
)
def test_redact_api_key(url: str, expected: str) -> None:
    """Test redact_api_key function."""
    assert openalex_client.redact_api_key(url) == expected


def test_redact_api_key_accepts_an_httpx_url() -> None:
    """The helper takes whatever an exception carries, not only strings."""
    redacted = openalex_client.redact_api_key(httpx.URL("https://api.openalex.org/works?api_key=secret"))

    assert "secret" not in redacted


def test_build_user_agent_announces_the_project() -> None:
    """The User-Agent names the project and carries no contact address."""
    user_agent = openalex_client.build_user_agent()

    assert user_agent.startswith("pub-analyzer/")
    # The polite pool is gone; an email in the User-Agent would be pointless and leaky.
    assert "mailto" not in user_agent


def test_create_client_sets_headers_and_timeout() -> None:
    """The client identifies itself and refuses to hang forever."""
    http_client = openalex_client.create_client()

    assert http_client.headers["User-Agent"].startswith("pub-analyzer/")
    assert http_client.timeout.read == openalex_client.DEFAULT_TIMEOUT.read
    assert http_client.timeout.read is not None


# --- Retries --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code",
    [
        httpx.codes.TOO_MANY_REQUESTS,
        httpx.codes.INTERNAL_SERVER_ERROR,
        httpx.codes.BAD_GATEWAY,
        httpx.codes.SERVICE_UNAVAILABLE,
        httpx.codes.GATEWAY_TIMEOUT,
    ],
)
async def test_get_json_retries_transient_statuses(status_code: int) -> None:
    """A transient status is retried and the eventual success is returned."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(SOURCE_URL)
        route.side_effect = [
            httpx.Response(status_code=status_code),
            httpx.Response(status_code=httpx.codes.OK, json={"ok": True}),
        ]

        assert await build_client().get_json(SOURCE_URL) == {"ok": True}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_get_json_retries_transport_errors() -> None:
    """A connection failure is retried."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(SOURCE_URL)
        route.side_effect = [
            httpx.ConnectError("boom"),
            httpx.Response(status_code=httpx.codes.OK, json={"ok": True}),
        ]

        assert await build_client().get_json(SOURCE_URL) == {"ok": True}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_get_json_gives_up_after_max_attempts() -> None:
    """Once attempts run out the last error surfaces."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.SERVICE_UNAVAILABLE))

        with pytest.raises(httpx.HTTPStatusError):
            await build_client(max_attempts=3).get_json(SOURCE_URL)

        assert route.call_count == 3


@pytest.mark.asyncio
async def test_get_json_does_not_retry_client_errors() -> None:
    """A 404 fails immediately rather than burning the retry budget."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.NOT_FOUND))

        with pytest.raises(httpx.HTTPStatusError):
            await build_client().get_json(SOURCE_URL)

        assert route.call_count == 1


@pytest.mark.asyncio
async def test_get_json_honours_retry_after() -> None:
    """A Retry-After header sets the delay before the next attempt."""
    client = build_client()
    client.initial_backoff = 100.0  # Would be picked if Retry-After were ignored.

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(SOURCE_URL)
        route.side_effect = [
            httpx.Response(status_code=httpx.codes.TOO_MANY_REQUESTS, headers={"Retry-After": "0"}),
            httpx.Response(status_code=httpx.codes.OK, json={"ok": True}),
        ]

        assert await client.get_json(SOURCE_URL) == {"ok": True}


@pytest.mark.parametrize(
    ["headers", "expected"],
    [
        pytest.param({"Retry-After": "12"}, 12.0, id="seconds"),
        pytest.param({"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}, None, id="http-date-unsupported"),
        pytest.param({}, None, id="missing"),
    ],
)
def test_parse_retry_after(headers: dict[str, str], expected: float | None) -> None:
    """Test _parse_retry_after function."""
    response = httpx.Response(status_code=httpx.codes.TOO_MANY_REQUESTS, headers=headers)

    assert openalex_client._parse_retry_after(response) == expected


def test_backoff_delay_grows_and_is_capped() -> None:
    """Backoff doubles per attempt, jittered, and never exceeds the ceiling."""
    client = build_client()
    client.initial_backoff = 1.0

    # Jitter keeps each delay within half of its nominal value.
    assert 0.5 <= client._backoff_delay(attempt=1, retry_after=None) <= 1.0
    assert 1.0 <= client._backoff_delay(attempt=2, retry_after=None) <= 2.0
    assert client._backoff_delay(attempt=50, retry_after=None) <= openalex_client.MAX_BACKOFF_SECONDS
    assert client._backoff_delay(attempt=1, retry_after=999.0) == openalex_client.MAX_BACKOFF_SECONDS


# --- Cursor pagination ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_works_single_page() -> None:
    """A single page ends the walk when the cursor runs out."""
    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith=WORKS_URL).mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK, WORK], next_cursor=None))
        )

        works = await build_client().get_works(WORKS_URL)

    assert len(works) == 2


@pytest.mark.asyncio
async def test_get_works_follows_the_cursor() -> None:
    """Every page is requested with the cursor the previous one handed back."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=WORKS_URL)
        route.side_effect = [
            httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor="cursor-2")),
            httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor="cursor-3")),
            httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor=None)),
        ]

        works = await build_client().get_works(WORKS_URL)

    assert len(works) == 3
    assert [call.request.url.params["cursor"] for call in route.calls] == ["*", "cursor-2", "cursor-3"]


@pytest.mark.asyncio
async def test_get_works_never_pages_by_number() -> None:
    """Page numbers cannot reach past 10.000 results, so they must not be used."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=WORKS_URL)
        route.side_effect = [
            httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor="cursor-2")),
            httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor=None)),
        ]

        await build_client().get_works(WORKS_URL)

    assert all("page" not in call.request.url.params for call in route.calls)


@pytest.mark.asyncio
async def test_get_works_stops_on_repeated_cursor() -> None:
    """An API that keeps handing back the same cursor does not trap us in a loop."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=WORKS_URL).mock(
            return_value=httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor="*"))
        )

        works = await build_client().get_works(WORKS_URL)

    assert route.call_count == 1
    assert len(works) == 1


@pytest.mark.asyncio
async def test_get_works_raises_on_error_status() -> None:
    """An error status surfaces instead of being read as an empty page."""
    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(url__startswith=WORKS_URL).mock(return_value=httpx.Response(status_code=httpx.codes.NOT_FOUND))

        with pytest.raises(httpx.HTTPStatusError):
            await build_client().get_works(WORKS_URL)


@pytest.mark.asyncio
async def test_get_works_raises_on_error_status_of_later_page() -> None:
    """An error on a page past the first is not swallowed."""
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.get(url__startswith=WORKS_URL)
        route.side_effect = [
            httpx.Response(status_code=httpx.codes.OK, json=works_page([WORK], next_cursor="cursor-2")),
            httpx.Response(status_code=httpx.codes.NOT_FOUND),
        ]

        with pytest.raises(httpx.HTTPStatusError):
            await build_client().get_works(WORKS_URL)


# --- Sources --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["homepage_url", "expected_homepage_url"],
    [
        pytest.param("https://example.org", "https://example.org/", id="valid-url-kept"),
        pytest.param("www.example.org", None, id="schemeless-url-discarded"),
        pytest.param(None, None, id="missing-url"),
    ],
)
async def test_get_source_homepage_url(homepage_url: str | None, expected_homepage_url: str | None) -> None:
    """Sources carrying a homepage URL without scheme have it discarded."""
    payload = dict(SOURCE) | {"homepage_url": homepage_url}

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.OK, json=payload))

        source = await build_client().get_source(SOURCE_URL)

    assert (str(source.homepage_url) if source.homepage_url else None) == expected_homepage_url


@pytest.mark.asyncio
async def test_get_source_without_homepage_key() -> None:
    """A payload missing the homepage key entirely is still accepted."""
    payload = {key: value for key, value in SOURCE.items() if key != "homepage_url"}

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get(SOURCE_URL).mock(return_value=httpx.Response(status_code=httpx.codes.OK, json=payload))

        assert await build_client().get_source(SOURCE_URL) is not None
