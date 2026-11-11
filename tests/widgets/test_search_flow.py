"""Test searching OpenAlex, including searches that are still pending when the input changes."""

from collections.abc import Callable
from typing import Any

import httpx2 as httpx
import pytest
from rich.table import Table
from textual.pilot import Pilot
from textual.widgets import Button, Label, Static

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets.author.core import AuthorSummaryWidget
from pub_analyzer.widgets.author.tables import AuthorWorksByYearTable
from pub_analyzer.widgets.common.summary import SummaryWidget
from pub_analyzer.widgets.institution.core import InstitutionSummaryWidget
from pub_analyzer.widgets.institution.tables import InstitutionWorksByYearTable
from pub_analyzer.widgets.report.core import LoadReportWidget
from pub_analyzer.widgets.search import AuthorResultWidget, FinderWidget, InstitutionResultWidget, SearchBar
from pub_analyzer.widgets.search.results import ResultWidget
from tests import http_mock
from tests.data.author import AUTHOR, AUTHOR_OPEN_ALEX_ID, AUTHOR_RESULT, AUTHOR_RESULT_OBJECT
from tests.data.institution import INSTITUTION, INSTITUTION_OPEN_ALEX_ID, INSTITUTION_RESULT, INSTITUTION_RESULT_OBJECT
from tests.widgets.helpers import page_title, wait_for_workers


def autocomplete_url(entity: str) -> str:
    """Return the OpenAlex autocomplete URL used to search authors or institutions."""
    return f"https://api.openalex.org/autocomplete/{entity}s"


def search_text(request: httpx.Request) -> str:
    """Return what an autocomplete request searches for."""
    return request.url.params["q"]


def results_response(*results: dict[str, Any]) -> httpx.Response:
    """Build an autocomplete response."""
    return httpx.Response(200, json={"results": list(results)})


async def search_institutions(pilot: Pilot) -> None:
    """Switch the search from authors to institutions, with the dropdown."""
    await pilot.click(FinderWidget.EntityTypeSelector)
    await pilot.press("down", "enter")

    assert pilot.app.query_one(SearchBar).placeholder == "Search institution"


async def type_in_search(pilot: Pilot, *keys: str) -> None:
    """Press keys in the search bar, then wait for the searches they start."""
    await pilot.press(*keys)
    await wait_for_workers(pilot)


def result_names(pilot: Pilot) -> list[str]:
    """Return the names of the results on screen."""
    return [str(result.query_one(Button).label) for result in pilot.app.query(ResultWidget)]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["entity", "result", "author_hint"],
    [
        pytest.param("author", AUTHOR_RESULT, "institution", id="author"),
        pytest.param("institution", INSTITUTION_RESULT, None, id="institution"),
    ],
)
async def test_typing_shows_matching_results(entity: str, result: dict[str, Any], author_hint: str | None) -> None:
    """Each key press searches OpenAlex, and the results show each match's name and hint."""
    with http_mock.mock() as openalex:
        searches = openalex.get(url__startswith=autocomplete_url(entity)).mock(return_value=results_response(result))

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            # Authors are searched by default; institutions have to be chosen.
            if entity == "institution":
                await search_institutions(pilot)

            assert await pilot.click(SearchBar)
            await type_in_search(pilot, "m", "a")

            assert result_names(pilot) == [result["display_name"]]
            assert str(pilot.app.query_one(".text-hint", Label).render()) == result["hint"]

    assert [search_text(call.request) for call in searches.calls] == ["m", "ma"]
    assert searches.calls[-1].request.url.params.get("author_hint") == author_hint


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["make_result", "details_url", "details", "summary_type", "table_type"],
    [
        pytest.param(
            lambda: AuthorResultWidget(AUTHOR_RESULT_OBJECT),
            f"https://api.openalex.org/authors/{AUTHOR_OPEN_ALEX_ID}",
            AUTHOR,
            AuthorSummaryWidget,
            AuthorWorksByYearTable,
            id="author",
        ),
        pytest.param(
            lambda: InstitutionResultWidget(INSTITUTION_RESULT_OBJECT),
            f"https://api.openalex.org/institutions/{INSTITUTION_OPEN_ALEX_ID}",
            INSTITUTION,
            InstitutionSummaryWidget,
            InstitutionWorksByYearTable,
            id="institution",
        ),
    ],
)
async def test_choosing_a_result_opens_its_summary(
    make_result: Callable[[], ResultWidget],
    details_url: str,
    details: dict[str, Any],
    summary_type: type[SummaryWidget],
    table_type: type[Static],
) -> None:
    """The summary replaces the search page, loads the details, and shows them."""
    result = make_result()

    with http_mock.mock() as openalex:
        openalex.get(details_url).mock(return_value=httpx.Response(200, json=details))
        details_gate = openalex.hold(lambda request: str(request.url) == details_url)

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            await pilot.app.query_one("#results-container").mount(result)
            await pilot.pause()
            assert await pilot.click(result.query_one(Button))

            # While the details load, the summary shows a loading indicator.
            await details_gate.reached()
            summary = pilot.app.query_one(summary_type)

            assert summary.loading
            assert not pilot.app.query(FinderWidget)
            assert page_title(pilot.app) == details["display_name"]

            # Once they arrive, the summary shows them and the report can be made.
            details_gate.open()
            await wait_for_workers(pilot)

            assert not summary.loading
            assert not summary.query_one("#make-report-button", Button).disabled

            counts_by_year = summary.query_one(table_type).query_one(Static).content
            assert isinstance(counts_by_year, Table)
            assert counts_by_year.row_count == len(details["counts_by_year"])


@pytest.mark.asyncio
async def test_results_are_cleared_when_nothing_matches() -> None:
    """Results disappear when a search finds nothing, and when the search bar is emptied."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Only "m" matches something."""
        return results_response(AUTHOR_RESULT) if search_text(request) == "m" else results_response()

    with http_mock.mock() as openalex:
        searches = openalex.get(url__startswith=autocomplete_url("author")).mock(side_effect=respond)

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            assert await pilot.click(SearchBar)

            await type_in_search(pilot, "m")
            assert result_names(pilot) == [AUTHOR_RESULT["display_name"]]

            # No matches clears the results.
            await type_in_search(pilot, "z")
            assert result_names(pilot) == []

            await type_in_search(pilot, "backspace")
            assert result_names(pilot) == [AUTHOR_RESULT["display_name"]]

            # So does emptying the search bar, without searching.
            await type_in_search(pilot, "backspace")
            assert result_names(pilot) == []

    assert [search_text(call.request) for call in searches.calls] == ["m", "mz", "m"]


def mock_author_searches(openalex: http_mock.MockRouter) -> http_mock.Gate:
    """Mock author searches, holding back the response to the first one, for "m".

    The search for "m" finds an author named "Old result"; any other search finds "New result".
    """

    def respond(request: httpx.Request) -> httpx.Response:
        name = "Old result" if search_text(request) == "m" else "New result"
        return results_response({**AUTHOR_RESULT, "display_name": name})

    openalex.get(url__startswith=autocomplete_url("author")).mock(side_effect=respond)
    return openalex.hold(lambda request: request.url.path.endswith("/authors") and search_text(request) == "m")


async def start_searching_m(pilot: Pilot, first_search: http_mock.Gate) -> None:
    """Type "m" in the search bar, and wait until that search is pending."""
    assert await pilot.click(SearchBar)
    await pilot.press("m")
    await first_search.reached()


@pytest.mark.asyncio
async def test_a_newer_search_replaces_a_pending_one() -> None:
    """Typing more while a search is pending cancels it, so only the newer results appear."""
    with http_mock.mock() as openalex:
        first_search = mock_author_searches(openalex)

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            await start_searching_m(pilot, first_search)

            await pilot.press("a")
            await first_search.cancelled()

            first_search.open()
            await wait_for_workers(pilot)
            assert result_names(pilot) == ["New result"]


@pytest.mark.asyncio
async def test_switching_to_institutions_discards_a_pending_author_search() -> None:
    """Switching the entity while an author search is pending cancels it and clears the search bar."""
    with http_mock.mock() as openalex:
        first_search = mock_author_searches(openalex)
        openalex.get(url__startswith=autocomplete_url("institution")).mock(return_value=results_response(INSTITUTION_RESULT))

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            await start_searching_m(pilot, first_search)

            await search_institutions(pilot)
            assert pilot.app.query_one(SearchBar).value == ""

            # Search institutions; the pending author search never shows up.
            assert await pilot.click(SearchBar)
            await pilot.press("m")
            await first_search.cancelled()

            first_search.open()
            await wait_for_workers(pilot)
            assert result_names(pilot) == [INSTITUTION_RESULT["display_name"]]
            assert not pilot.app.query(AuthorResultWidget)


@pytest.mark.asyncio
async def test_emptying_the_search_bar_discards_a_pending_search() -> None:
    """A pending search that finishes after the search bar is emptied shows nothing."""
    with http_mock.mock() as openalex:
        first_search = mock_author_searches(openalex)

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            await start_searching_m(pilot, first_search)
            await pilot.press("backspace")

            # The search finishes, but its results no longer match the search bar.
            first_search.open()
            await wait_for_workers(pilot)
            assert result_names(pilot) == []


@pytest.mark.asyncio
async def test_leaving_the_search_page_cancels_a_pending_search() -> None:
    """Going to another page while a search is pending cancels it."""
    with http_mock.mock() as openalex:
        first_search = mock_author_searches(openalex)

        async with PubAnalyzerApp().run_test(size=(120, 40)) as pilot:
            await start_searching_m(pilot, first_search)

            assert await pilot.click("#load-sidebar-button")
            await first_search.cancelled()

            first_search.open()
            await wait_for_workers(pilot)
            assert not pilot.app.query(FinderWidget)
            assert pilot.app.query_one(LoadReportWidget)
            assert page_title(pilot.app) == "Load report"
