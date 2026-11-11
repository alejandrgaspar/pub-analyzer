"""Strict HTTPX2 request routing for offline tests."""

import asyncio
from collections.abc import Callable, Iterable
from types import TracebackType
from typing import cast
from unittest.mock import patch

import httpx2 as httpx


class Call:
    """A request received by a route."""

    def __init__(self, request: httpx.Request) -> None:
        self.request = request


class Route:
    """A matching URL and its configured responses."""

    def __init__(self, url: str, *, prefix: bool) -> None:
        self.url = url
        self.prefix = prefix
        self.calls: list[Call] = []
        self.return_value: httpx.Response | None = None
        self._side_effect: Callable[[httpx.Request], httpx.Response] | Iterable[httpx.Response | Exception] | None = None
        self._responses = iter(())

    @property
    def call_count(self) -> int:
        """Number of requests received."""
        return len(self.calls)

    @property
    def side_effect(self) -> Callable[[httpx.Request], httpx.Response] | Iterable[httpx.Response | Exception] | None:
        """Return the configured response provider."""
        return self._side_effect

    @side_effect.setter
    def side_effect(self, value: Callable[[httpx.Request], httpx.Response] | Iterable[httpx.Response | Exception]) -> None:
        self._side_effect = value
        if not callable(value):
            self._responses = iter(value)

    def mock(
        self, *, return_value: httpx.Response | None = None, side_effect: Callable[[httpx.Request], httpx.Response] | None = None
    ) -> "Route":
        """Configure a constant response or a request handler."""
        self.return_value = return_value
        if side_effect is not None:
            self.side_effect = side_effect
        return self

    def respond(self, request: httpx.Request) -> httpx.Response:
        """Record a request and produce its response."""
        self.calls.append(Call(request))
        if callable(self._side_effect):
            handler = cast(Callable[[httpx.Request], httpx.Response], self._side_effect)
            result = handler(request)
        elif self._side_effect is not None:
            result = next(self._responses)
        else:
            result = self.return_value
        if isinstance(result, Exception):
            raise result
        assert isinstance(result, httpx.Response), f"No response configured for {request.url}"
        return result


class Gate:
    """Holds back the responses to matching requests until it is opened.

    This lets a test look at the app while a request is still in flight, and control which
    of two concurrent requests finishes first.
    """

    def __init__(self, matches: Callable[[httpx.Request], bool]) -> None:
        self.matches = matches
        self._reached = asyncio.Event()
        self._cancelled = asyncio.Event()
        self._opened = asyncio.Event()

    def open(self) -> None:
        """Let waiting and future matching requests through."""
        self._opened.set()

    async def reached(self) -> None:
        """Wait up to 10 seconds for a matching request to be held at the gate."""
        await asyncio.wait_for(self._reached.wait(), timeout=10)

    async def cancelled(self) -> None:
        """Wait up to 10 seconds for the app to cancel a request held at the gate."""
        await asyncio.wait_for(self._cancelled.wait(), timeout=10)

    async def hold(self) -> None:
        """Hold a matching request until the gate opens, noting if the app cancels it first."""
        self._reached.set()
        try:
            await asyncio.wait_for(self._opened.wait(), timeout=10)
        except asyncio.CancelledError:
            self._cancelled.set()
            raise


class MockRouter:
    """Intercept all async HTTP requests and reject unexpected or unused routes."""

    def __init__(self, *, assert_all_called: bool = True) -> None:
        self.assert_all_called = assert_all_called
        self.routes: list[Route] = []
        self.gates: list[Gate] = []
        self._patch = patch.object(httpx.AsyncHTTPTransport, "handle_async_request", self._handle)

    def hold(self, matches: Callable[[httpx.Request], bool]) -> Gate:
        """Hold back the responses to requests for which `matches` is true, until the gate opens."""
        gate = Gate(matches)
        self.gates.append(gate)
        return gate

    def get(self, url: str | None = None, *, url__startswith: str | None = None) -> Route:
        """Register a GET route with an exact URL or URL prefix."""
        assert (url is None) != (url__startswith is None)
        route = Route(url if url is not None else str(url__startswith), prefix=url__startswith is not None)
        self.routes.append(route)
        return route

    async def _handle(self, request: httpx.Request) -> httpx.Response:
        response = self._route(request)
        for gate in self.gates:
            if gate.matches(request):
                await gate.hold()
        return response

    def _route(self, request: httpx.Request) -> httpx.Response:
        for route in self.routes:
            url = str(request.url)
            if request.method == "GET" and (url.startswith(route.url) if route.prefix else url == route.url):
                return route.respond(request)
        raise AssertionError(f"Unexpected HTTP request: {request.method} {request.url}")

    def __enter__(self) -> "MockRouter":
        """Start intercepting requests."""
        self._patch.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        """Restore the transport and verify registered routes were used."""
        self._patch.stop()
        if exc_type is None and self.assert_all_called:
            assert all(route.calls for route in self.routes), "Some HTTP routes were not called"


def mock(*, assert_all_called: bool = True) -> MockRouter:
    """Create a strict request router."""
    return MockRouter(assert_all_called=assert_all_called)
