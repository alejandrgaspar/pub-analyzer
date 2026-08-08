"""Test the widget showing how far along a report is."""

import sys

import httpx
import pytest
import respx
from textual.app import App, ComposeResult
from textual.widgets import Label, ProgressBar

from pub_analyzer.internal.report.progress import ReportProgress, ReportStage
from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.models.author import Author
from pub_analyzer.widgets.body import MainContent
from pub_analyzer.widgets.report.core import CreateAuthorReportWidget, ReportProgressWidget
from tests.data.author import AUTHOR

if sys.platform == "win32":
    pytest.skip(
        "Skipping this module on Windows. GH runners for Windows are not reliable for verifying these types of tests.",
        allow_module_level=True,
    )


class _ProgressApp(App[None]):
    """Bare app hosting a lone progress widget.

    Deliberately not a `PubAnalyzerApp`: its `CSS_PATH` entries are relative to the module
    declaring them, so a subclass here would look for the stylesheets under `tests/`.
    """

    def compose(self) -> ComposeResult:
        """Compose the widget under test."""
        yield ReportProgressWidget()


@pytest.mark.asyncio
async def test_progress_widget_starts_indeterminate() -> None:
    """Before anything is known the bar has no total to work towards."""
    async with _ProgressApp().run_test() as pilot:
        widget = pilot.app.query_one(ReportProgressWidget)

        assert widget.query_one(ProgressBar).total is None


@pytest.mark.asyncio
async def test_progress_widget_shows_a_measured_stage() -> None:
    """A stage with a known size drives a real bar."""
    async with _ProgressApp().run_test() as pilot:
        widget = pilot.app.query_one(ReportProgressWidget)

        widget.update_progress(ReportProgress(ReportStage.citations, done=3, total=10))
        await pilot.pause()

        assert str(widget.query_one(Label).renderable) == "Retrieving citations 3/10"
        progress_bar = widget.query_one(ProgressBar)
        assert (progress_bar.progress, progress_bar.total) == (3, 10)


@pytest.mark.asyncio
async def test_progress_widget_returns_to_indeterminate() -> None:
    """A stage of unknown size after a measured one keeps the bar pulsing."""
    async with _ProgressApp().run_test() as pilot:
        widget = pilot.app.query_one(ReportProgressWidget)

        widget.update_progress(ReportProgress(ReportStage.citations, done=5, total=5))
        await pilot.pause()
        assert widget.query_one(ProgressBar).total == 5

        widget.update_progress(ReportProgress(ReportStage.sources, done=0, total=0))
        await pilot.pause()

        assert widget.query_one(ProgressBar).total is None
        assert str(widget.query_one(Label).renderable) == "Retrieving sources..."


@pytest.mark.asyncio
async def test_progress_widget_walks_the_stages() -> None:
    """Each stage replaces the last, ending on the final count."""
    async with _ProgressApp().run_test() as pilot:
        widget = pilot.app.query_one(ReportProgressWidget)

        for progress in [
            ReportProgress(ReportStage.works),
            ReportProgress(ReportStage.citations, done=0, total=2),
            ReportProgress(ReportStage.citations, done=2, total=2),
            ReportProgress(ReportStage.sources, done=1, total=4),
        ]:
            widget.update_progress(progress)
            await pilot.pause()

        assert str(widget.query_one(Label).renderable) == "Retrieving sources 1/4"
        progress_bar = widget.query_one(ProgressBar)
        assert (progress_bar.progress, progress_bar.total) == (1, 4)


@pytest.mark.asyncio
async def test_report_view_shows_progress_instead_of_a_spinner() -> None:
    """Building a report leads with the progress widget, not an endless spinner."""
    async with PubAnalyzerApp().run_test() as pilot:
        with respx.mock(assert_all_called=True) as respx_mock:
            respx_mock.get(url__startswith="https://api.openalex.org/works").mock(
                return_value=httpx.Response(
                    status_code=httpx.codes.OK,
                    json={"meta": {"count": 0, "per_page": 200, "next_cursor": None}, "results": []},
                )
            )

            main_content = pilot.app.query_one(MainContent)
            await main_content.mount(CreateAuthorReportWidget(author=Author(**AUTHOR)))
            await pilot.pause()

            assert pilot.app.query(ReportProgressWidget), "the report view should show progress"
            assert not pilot.app.query("LoadingIndicator"), "the indefinite spinner should be gone"
