"""Main Report widgets."""

import pathlib

from pydantic import TypeAdapter
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, LoadingIndicator, Static, TabbedContent, TabPane

from pub_analyzer.internal.report import make_author_report, make_institution_report
from pub_analyzer.models.author import Author
from pub_analyzer.models.institution import Institution
from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.widgets.common import FileSystemSelector

from .author import AuthorReportPane
from .export import ExportReportPane
from .source import SourcesReportPane
from .work import WorkReportPane


class ReportWidget(Static):
    """Base report widget."""


class AuthorReportWidget(ReportWidget):
    """Author report generator view."""

    def __init__(self, report: AuthorReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and with all the widgets."""
        with TabbedContent(id="main-container"):
            with TabPane("Author"):
                yield AuthorReportPane(report=self.report)
            with TabPane("Works"):
                yield WorkReportPane(report=self.report)
            with TabPane("Sources"):
                yield SourcesReportPane(report=self.report)
            with TabPane("Export"):
                suggest_prefix = self.report.author.display_name.lower().split()[0]
                yield ExportReportPane(report=self.report, suggest_prefix=suggest_prefix)


class InstitutionReportWidget(ReportWidget):
    """Institution report generator view."""

    def __init__(self, report: InstitutionReport) -> None:
        self.report = report
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and with all the widgets."""
        with TabbedContent(id="main-container"):
            with TabPane("Works"):
                yield WorkReportPane(report=self.report)
            with TabPane("Sources"):
                yield SourcesReportPane(report=self.report)
            with TabPane("Export"):
                suggest_prefix = self.report.institution.display_name.lower().replace(" ", "-")
                yield ExportReportPane(report=self.report, suggest_prefix=suggest_prefix)


class CreateReportWidget(Static):
    """Base Widget report wrapper to load data from API."""

    def compose(self) -> ComposeResult:
        """Create main info container and showing a loading animation."""
        yield LoadingIndicator()
        yield Container()

    def on_mount(self) -> None:
        """Hiding the empty container and calling the data in the background."""
        self.query_one(Container).display = False
        self.run_worker(self.mount_report(), exclusive=True)

    async def make_report(self) -> Widget:
        """Make report and create the widget."""
        raise NotImplementedError

    async def mount_report(self) -> None:
        """Mount report."""
        report_widget = await self.make_report()
        container = self.query_one(Container)
        await container.mount(report_widget)

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True



class CreateAuthorReportWidget(CreateReportWidget):
    """Widget Author report wrapper to load data from API."""

    def __init__(self, author: Author, works_api_url: str) -> None:
        self.works_api_url = works_api_url
        self.author = author

        super().__init__()

    async def make_report(self) -> AuthorReportWidget:
        """Make report and create the widget."""
        report = await make_author_report(author=self.author)
        return AuthorReportWidget(report=report)


class CreateInstitutionReportWidget(CreateReportWidget):
    """Widget Institution report wrapper to load data from API."""

    def __init__(self, institution: Institution, works_api_url: str) -> None:
        self.works_api_url = works_api_url
        self.institution = institution

        super().__init__()

    async def make_report(self) -> InstitutionReportWidget:
        """Make report and create the widget."""
        report = await make_institution_report(institution=self.institution)
        return InstitutionReportWidget(report=report)


class LoadReportWidget(Static):
    """Widget report wrapper to load data from disk."""

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
            report: AuthorReport = TypeAdapter(AuthorReport).validate_json(data)
        report_widget = AuthorReportWidget(report=report)

        main_content = self.app.query_one(MainContent)
        await main_content.query("*").exclude("#page-title").remove()
        await main_content.mount(report_widget)

        main_content.update_title(title=report.author.display_name)

    def compose(self) -> ComposeResult:
        """Compose load report widget."""
        yield FileSystemSelector(path=pathlib.Path.home(), only_dir=False, extension=[".json",])

        with Horizontal(classes="button-container"):
            yield Button("Load Report", variant="primary", disabled=True, id="load-report-button")
