"""Main Report widgets."""

import pathlib

from pydantic import TypeAdapter
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, LoadingIndicator, Static, TabbedContent, TabPane

from pub_analyzer.models.author import Author
from pub_analyzer.models.report import Report
from pub_analyzer.utils.report import make_report
from pub_analyzer.widgets.common import FileSystemSelector

from .author import AuthorReportPane
from .export import ExportReportPane
from .source import SourcesReportPane
from .work import WorkReportPane


class ReportWidget(Static):
    """Report generator view."""

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and showing a loading animation."""
        with TabbedContent(id="main-container"):
            with TabPane("Author"):
                yield AuthorReportPane(report=self.report)
            with TabPane("Works"):
                yield WorkReportPane(report=self.report)
            with TabPane("Sources"):
                yield SourcesReportPane(report=self.report)
            with TabPane("Export"):
                yield ExportReportPane(report=self.report)


class CreateReportWidget(Static):
    """Create Report Widget."""

    def __init__(self, author: Author, works_api_url: str) -> None:
        self.works_api_url = works_api_url
        self.author = author

        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and showing a loading animation."""
        yield LoadingIndicator()
        yield Container()

    def on_mount(self) -> None:
        """Hiding the empty container and calling the data in the background."""
        self.query_one(Container).display = False
        self.run_worker(self.make_report(), exclusive=True)

    async def make_report(self) -> None:
        """Generate the report and compose the widget."""
        report = await make_report(author=self.author)
        container = self.query_one(Container)
        await container.mount(ReportWidget(report=report))

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True


class LoadReportWidget(Static):
    """Load report view."""

    @on(FileSystemSelector.FileSelected)
    def enable_button(self, event: FileSystemSelector.FileSelected) -> None:
        """Enable button on file select."""
        if event.file_selected:
            self.query_one(Button).disabled = False
        else:
            self.query_one(Button).disabled = True

    @on(Button.Pressed, "#load-report-button")
    async def load_report(self) -> None:
        """Load Report."""
        from pub_analyzer.widgets.body import MainContent

        file_path = self.query_one(FileSystemSelector).path_selected
        if not file_path:
            return

        with open(file_path) as file:
            data = file.read()
            report: Report = TypeAdapter(Report).validate_json(data)
        report_widget = ReportWidget(report=report)

        main_content = self.app.query_one(MainContent)
        await main_content.query("*").exclude("#page-title").remove()
        await main_content.mount(report_widget)

        main_content.update_title(title=report.author.display_name)

    def compose(self) -> ComposeResult:
        """Compose load report widget."""
        yield FileSystemSelector(path=pathlib.Path.home(), only_dir=False)

        with Horizontal(classes="button-container"):
            yield Button("Load Report", variant="primary", disabled=True, id="load-report-button")
