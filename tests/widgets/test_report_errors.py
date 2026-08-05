"""Test the failure messages shown when a report cannot be generated."""

import httpx
import pytest

from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR
from pub_analyzer.widgets.report.core import build_report_error_message

REQUEST = httpx.Request("GET", "https://api.openalex.org/works?filter=x&api_key=secret-key")


def status_error(status_code: int) -> httpx.HTTPStatusError:
    """Build an HTTPStatusError carrying a request with an API key."""
    return httpx.HTTPStatusError("boom", request=REQUEST, response=httpx.Response(status_code=status_code, request=REQUEST))


@pytest.mark.parametrize(
    "status_code",
    [httpx.codes.UNAUTHORIZED, httpx.codes.FORBIDDEN, httpx.codes.CONFLICT, httpx.codes.TOO_MANY_REQUESTS],
)
def test_authentication_failures_point_at_the_api_key(status_code: int) -> None:
    """A rejected request tells the user which variable to set."""
    message = build_report_error_message(status_error(status_code))

    assert API_KEY_ENV_VAR in message
    assert "openalex.org/settings/api" in message


def test_other_failures_keep_the_generic_message() -> None:
    """A server error is not blamed on the API key."""
    message = build_report_error_message(status_error(httpx.codes.INTERNAL_SERVER_ERROR))

    assert API_KEY_ENV_VAR not in message
    assert "500" in message


def test_transport_failures_are_reported() -> None:
    """A connection failure is explained rather than crashing the worker."""
    message = build_report_error_message(httpx.ConnectError("no route to host"))

    assert "could not be reached" in message


@pytest.mark.parametrize(
    "exc",
    [
        pytest.param(status_error(httpx.codes.TOO_MANY_REQUESTS), id="authentication"),
        pytest.param(status_error(httpx.codes.INTERNAL_SERVER_ERROR), id="server-error"),
    ],
)
def test_messages_never_leak_the_api_key(exc: httpx.HTTPStatusError) -> None:
    """The key rides on the request URL, so it must be scrubbed before display."""
    message = build_report_error_message(exc)

    assert "secret-key" not in message
    assert "REDACTED" in message
