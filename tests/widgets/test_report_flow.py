"""Test building a report: its progress, the finished report, errors and cancellation."""

from collections.abc import Callable

import httpx2 as httpx
import pytest
from textual.pilot import Pilot
from textual.widgets import Label, ProgressBar

from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR
from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets.body import MainContent
from pub_analyzer.widgets.report.core import (
    AuthorReportWidget,
    CreateAuthorReportWidget,
    CreateInstitutionReportWidget,
    CreateReportWidget,
    InstitutionReportWidget,
    ReportProgressWidget,
    ReportWidget,
)
from pub_analyzer.widgets.search import FinderWidget
from tests import http_mock
from tests.data.author import AUTHOR_OBJECT
from tests.data.builders import make_work
from tests.data.institution import INSTITUTION_OBJECT
from tests.widgets.helpers import page_title, spy_on_notifications, wait_for_workers

WORKS_URL = "https://api.openalex.org/works"


def is_citations_request(request: httpx.Request) -> bool:
    """Whether the request asks for the works that cite another work."""
    return request.url.params["filter"].startswith("cites:")


def works_response(request: httpx.Request) -> httpx.Response:
    """Answer OpenAlex works requests.

    The entity has two works, and only the second is cited, so building the report makes one
    request for the works and one for the citations of the second work. That citation request
    finds nothing.
    """
    works = []
    if not is_citations_request(request):
        works = [
            make_work("W1", title="First work", publication_date="2020-01-01"),
            make_work("W2", title="Second work", publication_date="2020-01-02", cited_by_count=1),
        ]

    return httpx.Response(
        200,
        json={
            "meta": {"count": len(works), "per_page": 200, "next_cursor": None},
            "results": [work.model_dump(mode="json") for work in works],
        },
    )


async def start_building(pilot: Pilot, creator: CreateReportWidget) -> None:
    """Show the report builder in place of the search page, which starts building the report."""
    await pilot.app.query_one(FinderWidget).remove()
    await pilot.app.query_one(MainContent).mount(creator)


def progress_text(progress: ReportProgressWidget) -> str:
    """Return the text describing the current stage."""
    return str(progress.query_one(Label).render())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["make_creator", "report_widget", "openalex_id"],
    [
        pytest.param(lambda: CreateAuthorReportWidget(author=AUTHOR_OBJECT), AuthorReportWidget, "A5090292188", id="author"),
        pytest.param(
            lambda: CreateInstitutionReportWidget(institution=INSTITUTION_OBJECT), InstitutionReportWidget, "I916541031", id="institution"
        ),
    ],
)
async def test_progress_is_shown_until_the_report_is_ready(
    make_creator: Callable[[], CreateReportWidget],
    report_widget: type[ReportWidget],
    openalex_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The progress follows each stage of the build, then gives way to the finished report."""
    creator = make_creator()
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    with http_mock.mock() as openalex:
        works = openalex.get(url__startswith=WORKS_URL).mock(side_effect=works_response)
        works_gate = openalex.hold(lambda request: not is_citations_request(request))
        citations_gate = openalex.hold(is_citations_request)

        async with app.run_test(size=(120, 40)) as pilot:
            await start_building(pilot, creator)
            progress = creator.query_one(ReportProgressWidget)
            bar = progress.query_one(ProgressBar)

            # While the works are fetched, the total is still unknown.
            await works_gate.reached()
            await pilot.pause()

            assert progress.display
            assert progress_text(progress) == "Retrieving works..."
            assert bar.total is None

            # While the citations are fetched, the progress counts the works done.
            works_gate.open()
            await citations_gate.reached()
            await pilot.pause()

            assert progress_text(progress) == "Retrieving citations 1/2"
            assert (bar.progress, bar.total) == (1, 2)
            assert not creator.query(report_widget)

            # When the build is done, the report replaces the progress.
            citations_gate.open()
            await wait_for_workers(pilot)

            assert not progress.display
            report = creator.query_one(report_widget).report
            assert [work.work.title for work in report.works] == ["First work", "Second work"]

    assert works.call_count == 2
    assert openalex_id in works.calls[0].request.url.params["filter"]

    notify.assert_called_once()
    assert notify.call_args.kwargs["title"] == "Report created!"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_creator",
    [
        pytest.param(lambda: CreateAuthorReportWidget(author=AUTHOR_OBJECT), id="author"),
        pytest.param(lambda: CreateInstitutionReportWidget(institution=INSTITUTION_OBJECT), id="institution"),
    ],
)
async def test_a_rejected_request_explains_the_error(
    make_creator: Callable[[], CreateReportWidget],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When OpenAlex rejects a request, the progress goes away and an error names the API key variable, never the key."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "test-secret-key")
    creator = make_creator()
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    with http_mock.mock() as openalex:
        openalex.get(url__startswith=WORKS_URL).mock(return_value=httpx.Response(401))

        async with app.run_test(size=(120, 40)) as pilot:
            await start_building(pilot, creator)
            await wait_for_workers(pilot)

            assert not creator.query_one(ReportProgressWidget).display
            assert not creator.query(ReportWidget)

    notify.assert_called_once()
    notification = notify.call_args.kwargs
    assert notification["title"] == "Error making report!"
    assert notification["severity"] == "error"
    assert API_KEY_ENV_VAR in notification["message"]
    assert "test-secret-key" not in notification["message"]


@pytest.mark.asyncio
async def test_leaving_the_page_cancels_the_report(monkeypatch: pytest.MonkeyPatch) -> None:
    """A report still being built when the user leaves is cancelled: it never appears, and nothing is announced."""
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    with http_mock.mock() as openalex:
        openalex.get(url__startswith=WORKS_URL).mock(side_effect=works_response)
        citations_gate = openalex.hold(is_citations_request)

        async with app.run_test(size=(120, 40)) as pilot:
            await start_building(pilot, CreateAuthorReportWidget(author=AUTHOR_OBJECT))
            await citations_gate.reached()

            # Go back to the search page while the citations are still being fetched.
            assert await pilot.click("#search-sidebar-button")
            await citations_gate.cancelled()

            citations_gate.open()
            await wait_for_workers(pilot)

            assert app.query_one(FinderWidget)
            assert not app.query(CreateAuthorReportWidget)
            assert not app.query(AuthorReportWidget)
            assert page_title(app) == "Search"

    notify.assert_not_called()
