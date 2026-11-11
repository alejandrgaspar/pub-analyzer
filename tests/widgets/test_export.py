"""Test exporting a report to a file."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from textual.pilot import Pilot
from textual.widgets import Button

from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.widgets.common import Input
from pub_analyzer.widgets.report import export
from pub_analyzer.widgets.report.export import ExportReportPane
from tests.data.builders import make_author_report, make_institution_report
from tests.widgets.helpers import WidgetApp, click_when_ready, open_file_picker, spy_on_notifications, wait_for_workers

JSON = ExportReportPane.ExportFileType.JSON
PDF = ExportReportPane.ExportFileType.PDF


class FixedDateTime(datetime):
    """A `datetime` that is always 2024-02-03, so the suggested file names are predictable."""

    @classmethod
    def now(cls, tz=None) -> "FixedDateTime":
        """Return noon on 2024-02-03."""
        return cls(2024, 2, 3, 12, tzinfo=tz)


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the export pane suggest file names dated 2024-02-03."""
    monkeypatch.setattr(export, "datetime", FixedDateTime)


@pytest.fixture
def destination(home: Path) -> Path:
    """An empty directory to export to, the only entry in the file picker."""
    path = home / "destination"
    path.mkdir()
    return path


@pytest.fixture
def render_pdf(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Replace the PDF renderer with a mock."""
    render = Mock()
    monkeypatch.setattr(export, "render_report", render)
    return render


async def choose_destination(pilot: Pilot) -> None:
    """Choose the `destination` directory in the file picker."""
    _, tree = await open_file_picker(pilot)
    tree.focus()
    await pilot.press("home", "down")

    assert await pilot.click("#done-button")
    await pilot.pause()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["make_report", "prefix"],
    [
        pytest.param(make_author_report, "author", id="author"),
        pytest.param(make_institution_report, "institution", id="institution"),
    ],
)
async def test_json_export_writes_the_report(
    make_report: Callable[[], AuthorReport | InstitutionReport],
    prefix: str,
    destination: Path,
    render_pdf: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exported file holds the whole report, in the format that Load report reads back."""
    report = make_report()
    pane = ExportReportPane(report, suggest_prefix=prefix)
    app = WidgetApp(pane)
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(120, 50)) as pilot:
        file_name = pane.query_one(Input)
        export_button = pane.query_one("#export-report-button", Button)

        # The pane suggests a dated JSON file, and can't export until a destination is chosen.
        assert file_name.value == f"{prefix}-02-03-2024.json"
        assert pane.query_one(ExportReportPane.ExportTypeSelector).value is JSON
        assert export_button.disabled

        await choose_destination(pilot)
        assert not export_button.disabled

        # Export under a non-ASCII file name.
        file_name.value = "résumé.json"
        await click_when_ready(pilot, export_button)
        await wait_for_workers(pilot)

        assert export_button.disabled

    output = destination / "résumé.json"
    assert json.loads(output.read_text(encoding="utf-8")) == report.model_dump(mode="json", by_alias=True)
    render_pdf.assert_not_called()

    notify.assert_called_once()
    assert notify.call_args.kwargs["title"] == "Report exported successfully!"
    assert str(output) in notify.call_args.kwargs["message"]


@pytest.mark.asyncio
async def test_pdf_export_renders_the_report(destination: Path, render_pdf: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Choosing PDF changes the suggested file name, and exporting renders the report to that file."""
    report = make_author_report()
    pane = ExportReportPane(report, suggest_prefix="author")
    app = WidgetApp(pane)
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(120, 50)) as pilot:
        # Choose PDF with the keyboard.
        file_type = pane.query_one(ExportReportPane.ExportTypeSelector)
        file_type.focus()
        await pilot.press("enter", "down", "enter")

        assert file_type.value is PDF
        assert pane.query_one(Input).value == "author-02-03-2024.pdf"

        # Export.
        await choose_destination(pilot)
        await click_when_ready(pilot, pane.query_one("#export-report-button", Button))
        await wait_for_workers(pilot)

    render_pdf.assert_called_once_with(report=report, file_path=destination / "author-02-03-2024.pdf")
    assert notify.call_args.kwargs["title"] == "Report exported successfully!"


@pytest.mark.asyncio
@pytest.mark.usefixtures("home")
async def test_institution_reports_can_only_be_exported_as_json() -> None:
    """The file type can't be changed for an institution report."""
    pane = ExportReportPane(make_institution_report(), suggest_prefix="institution")

    async with WidgetApp(pane).run_test(size=(120, 50)) as pilot:
        file_type = pane.query_one(ExportReportPane.ExportTypeSelector)
        assert file_type.disabled

        # Trying to choose PDF anyway changes nothing.
        await pilot.click(file_type)
        await pilot.press("down", "enter")

        assert file_type.value is JSON
        assert not file_type.expanded


@pytest.mark.asyncio
async def test_export_does_nothing_without_a_file_name(destination: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With the file name cleared, Export writes nothing and shows no message."""
    pane = ExportReportPane(make_author_report(), suggest_prefix="author")
    app = WidgetApp(pane)
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test(size=(120, 50)) as pilot:
        await choose_destination(pilot)
        pane.query_one(Input).value = ""

        await click_when_ready(pilot, pane.query_one("#export-report-button", Button))
        await pilot.pause()

    assert not list(destination.iterdir())
    notify.assert_not_called()
