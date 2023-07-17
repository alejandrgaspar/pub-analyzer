"""Export report widget."""

import pathlib
from datetime import datetime

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label

from pub_analyzer.models.report import Report
from pub_analyzer.widgets.common import FileSystemSelector


class ExportReportPane(VerticalScroll):
    """Export report pane Widget."""

    DEFAULT_CSS = """
    ExportReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;
    }
    """

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    @on(Button.Pressed, "#export-report-button")
    def export_report(self) -> None:
        """Export Report."""
        export_path = self.query_one(FileSystemSelector).path_selected
        file_name = self.query_one(Input).value

        if export_path and file_name:
            file_path = export_path.joinpath(file_name)
            with open(file_path, mode="w") as file:
                file.write(self.report.model_dump_json(indent=2))

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        suggest_file_name = f"{self.report.author.display_name.lower().split()[0]}-{datetime.now().strftime('%m-%d-%Y')}.json"

        with Vertical(id="export-form"):
            with Vertical(classes="export-form-input-container"):
                yield Label("[b]Name File:[/]", classes="export-form-label")
                yield Input(value=suggest_file_name,placeholder="report.json", classes="export-form-input")

            with Vertical(classes="export-form-input-container"):
                yield Label("[b]Export Directory:[/]", classes="export-form-label")
                yield FileSystemSelector(path=pathlib.Path.home(), only_dir=True)

            with Horizontal(classes="export-form-buttons"):
                yield Button("Export Report", variant="primary", id="export-report-button")
