"""Test loading a saved report from a file."""

from collections.abc import Callable
from pathlib import Path

import pytest
from textual.pilot import Pilot
from textual.widgets import Button, TabbedContent

from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.widgets.common import FileSystemSelector
from pub_analyzer.widgets.report.core import AuthorReportWidget, InstitutionReportWidget, LoadReportWidget, ReportWidget
from tests.data.author import AUTHOR
from tests.data.builders import make_author_report, make_institution_report
from tests.data.institution import INSTITUTION
from tests.widgets.helpers import click_when_ready, node_path, open_file_picker, page_title, spy_on_notifications, wait_until


async def open_loader(pilot: Pilot) -> LoadReportWidget:
    """Go to the Load report page through the sidebar."""
    assert await pilot.click("#load-sidebar-button")
    await wait_until(pilot, lambda: bool(pilot.app.query(LoadReportWidget)))

    return pilot.app.query_one(LoadReportWidget)


async def choose_institution_reports(pilot: Pilot, loader: LoadReportWidget) -> None:
    """Switch the loader from author to institution reports, with the keyboard."""
    loader.query_one(LoadReportWidget.EntityTypeSelector).focus()
    await pilot.press("enter", "down", "enter")

    assert loader.entity_handler is LoadReportWidget.EntityType.INSTITUTION


async def choose_file(pilot: Pilot, path: Path) -> None:
    """Choose `path`, which must be the only JSON file in the home directory, in the file picker."""
    _, tree = await open_file_picker(pilot)
    assert [node_path(node) for node in tree.root.children] == [path]

    tree.focus()
    await pilot.press("home", "down", "enter")
    assert await pilot.click("#done-button")
    await pilot.pause()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["make_report", "report_widget", "title"],
    [
        pytest.param(make_author_report, AuthorReportWidget, AUTHOR["display_name"], id="author"),
        pytest.param(make_institution_report, InstitutionReportWidget, INSTITUTION["display_name"], id="institution"),
    ],
)
async def test_loading_a_report_shows_it(
    make_report: Callable[[], AuthorReport | InstitutionReport],
    report_widget: type[AuthorReportWidget] | type[InstitutionReportWidget],
    title: str,
    home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The chosen report replaces the Load report page, with all its data and its title."""
    report = make_report()
    path = home / "résumé.json"
    path.write_text(report.model_dump_json(by_alias=True), encoding="utf-8")
    (home / "notes.txt").write_text("Not a report", encoding="utf-8")

    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        load_button = loader.query_one("#load-report-button", Button)
        assert page_title(app) == "Load report"
        assert load_button.disabled

        # Author reports are the default; institution reports have to be chosen.
        if isinstance(report, InstitutionReport):
            await choose_institution_reports(pilot, loader)

        await choose_file(pilot, path)
        await click_when_ready(pilot, load_button)
        await wait_until(pilot, lambda: bool(app.query(report_widget)))

        # The report replaces the loader, with the same data it was saved with.
        loaded = app.query_one(report_widget)
        assert not app.query(LoadReportWidget)
        assert page_title(app) == title
        assert loaded.report.model_dump(mode="json", by_alias=True) == report.model_dump(mode="json", by_alias=True)
        assert loaded.query_one("#main-container", TabbedContent).tab_count == 4

    notify.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_report_shows_an_error_and_can_be_retried(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A report that doesn't match the chosen type is rejected, and the page stays ready to try again.

    Malformed JSON and a wrong schema fail validation in the same place as this case, an
    institution report loaded as an author report, so it covers them too.
    """
    path = home / "report.json"
    path.write_text(make_institution_report().model_dump_json(by_alias=True), encoding="utf-8")

    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(140, 60)) as pilot:
        loader = await open_loader(pilot)
        load_button = loader.query_one("#load-report-button", Button)
        await choose_file(pilot, path)

        # Loading it as an author report fails with an error message.
        await click_when_ready(pilot, load_button)
        await wait_until(pilot, lambda: notify.called)

        assert notify.call_args.kwargs["title"] == "Error loading report!"
        assert notify.call_args.kwargs["severity"] == "error"

        # Nothing else changes.
        assert app.query_one(LoadReportWidget) is loader
        assert not app.query(ReportWidget)
        assert page_title(app) == "Load report"
        assert loader.query_one(FileSystemSelector).path_selected == path

        # After fixing the file, loading it again works.
        report = make_author_report()
        path.write_text(report.model_dump_json(by_alias=True), encoding="utf-8")
        await click_when_ready(pilot, load_button)
        await wait_until(pilot, lambda: bool(app.query(AuthorReportWidget)))

        assert app.query_one(AuthorReportWidget).report == report
        assert page_title(app) == report.author.display_name

    notify.assert_called_once()
