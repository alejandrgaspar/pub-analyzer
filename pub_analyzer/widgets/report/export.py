"""Export report widget."""

import pathlib
from datetime import datetime
from enum import Enum

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label

from pub_analyzer.internal.render import render_report
from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.widgets.common import FileSystemSelector, Input, Select


class ExportReportPane(VerticalScroll):
    """Export report pane Widget."""

    DEFAULT_CSS = """
    ExportReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;
    }
    """

    class ExportFileType(Enum):
        """File types."""

        JSON = 0
        PDF = 1

    class ExportTypeSelector(Select[ExportFileType]):
        """Export file type selector."""

    def __init__(self, report: AuthorReport | InstitutionReport, suggest_prefix: str = "") -> None:
        self.report = report
        self.suggest_prefix = suggest_prefix
        super().__init__()

    @on(Select.Changed)
    async def on_select_entity(self, event: Select.Changed) -> None:
        """Change entity endpoint."""
        file_name_input = self.query_one(Input)
        match event.value:
            case self.ExportFileType.JSON:
                file_name_input.value = f"{self.suggest_prefix}-{datetime.now().strftime('%m-%d-%Y')}.json"

            case self.ExportFileType.PDF:
                file_name_input.value = f"{self.suggest_prefix}-{datetime.now().strftime('%m-%d-%Y')}.pdf"

    @on(FileSystemSelector.FileSelected)
    def enable_button(self, event: FileSystemSelector.FileSelected) -> None:
        """Enable button on file select."""
        if event.file_selected:
            self.query_one(Button).disabled = False
        else:
            self.query_one(Button).disabled = True

    @on(Button.Pressed, "#export-report-button")
    async def export_report(self) -> None:
        """Export Report."""
        export_path = self.query_one(FileSystemSelector).path_selected
        file_name = self.query_one(Input).value
        file_type = self.query_one(self.ExportTypeSelector).value

        if export_path and file_name:
            file_path = export_path.joinpath(file_name)

            match file_type:
                case self.ExportFileType.JSON:
                    with open(file_path, mode="w") as file:
                        file.write(self.report.model_dump_json(indent=2, by_alias=True))
                case self.ExportFileType.PDF:
                    report_bytes = await render_report(report=self.report, file_path=file_path)
                    with open(file_path, mode="wb") as file:
                        file.write(report_bytes)

            self.query_one(Button).disabled = True
            self.app.notify(
                title="Report exported successfully!",
                message=f"The report was exported correctly. You can go see it at [i]{file_path}[/]",
                timeout=20.0
            )

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        suggest_file_name = f"{self.suggest_prefix}-{datetime.now().strftime('%m-%d-%Y')}.json"

        with Vertical(id="export-form"):
            with Vertical(classes="export-form-input-container"):
                yield Label("[b]Name File:[/]", classes="export-form-label")
                with Horizontal(classes="file-selector-container"):
                    type_options = [(name, value) for name, value in self.ExportFileType.__members__.items()]

                    yield Input(value=suggest_file_name,placeholder="report.json", classes="export-form-input")
                    yield self.ExportTypeSelector(options=type_options, value=self.ExportFileType.JSON, allow_blank=False)

            with Vertical(classes="export-form-input-container"):
                yield Label("[b]Export Directory:[/]", classes="export-form-label")
                yield FileSystemSelector(path=pathlib.Path.home(), only_dir=True)

            with Horizontal(classes="export-form-buttons"):
                yield Button("Export Report", variant="primary", disabled=True, id="export-report-button")
