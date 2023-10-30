"""Main Report widgets."""

import datetime
import pathlib
from enum import Enum

import httpx
from pydantic import TypeAdapter, ValidationError
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, LoadingIndicator, Static, TabbedContent, TabPane

from pub_analyzer.internal.report import FromDate, ToDate, make_author_report, make_institution_report
from pub_analyzer.models.author import Author
from pub_analyzer.models.institution import Institution
from pub_analyzer.models.report import AuthorReport, InstitutionReport
from pub_analyzer.widgets.common import FileSystemSelector, Select

from .author import AuthorReportPane
from .export import ExportReportPane
from .institution import InstitutionReportPane
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
            with TabPane("Institution"):
                yield InstitutionReportPane(report=self.report)
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
        try:
            report_widget = await self.make_report()
        except httpx.HTTPStatusError as exc:
            self.query_one(LoadingIndicator).display = False
            status_error = f"HTTP Exception for url: {exc.request.url}. Status code: {exc.response.status_code}"
            self.app.notify(
                    title="Error making report!",
                    message=f"The report could not be generated due to a problem with the OpenAlex API. {status_error}",
                    severity="error",
                    timeout=20.0
                )
            return None

        container = self.query_one(Container)
        await container.mount(report_widget)

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True


class CreateAuthorReportWidget(CreateReportWidget):
    """Widget Author report wrapper to load data from API."""

    def __init__(
            self, author: Author, pub_from_date: datetime.datetime | None = None, pub_to_date: datetime.datetime | None = None,
            cited_from_date: datetime.datetime | None = None, cited_to_date: datetime.datetime | None = None
        ) -> None:
        self.author = author

        # Author publication date range
        self.pub_from_date = pub_from_date
        self.pub_to_date = pub_to_date

        # Cited date range
        self.cited_from_date = cited_from_date
        self.cited_to_date = cited_to_date

        super().__init__()

    async def make_report(self) -> AuthorReportWidget:
        """Make report and create the widget."""
        pub_from_date = FromDate(self.pub_from_date) if self.pub_from_date else None
        pub_to_date = ToDate(self.pub_to_date) if self.pub_to_date else None

        cited_from_date = FromDate(self.cited_from_date) if self.cited_from_date else None
        cited_to_date = ToDate(self.cited_to_date) if self.cited_to_date else None

        report = await make_author_report(
            author=self.author, pub_from_date=pub_from_date, pub_to_date=pub_to_date,
            cited_from_date=cited_from_date, cited_to_date=cited_to_date
        )
        return AuthorReportWidget(report=report)


class CreateInstitutionReportWidget(CreateReportWidget):
    """Widget Institution report wrapper to load data from API."""

    def __init__(
            self, institution: Institution, pub_from_date: datetime.datetime | None = None, pub_to_date: datetime.datetime | None = None,
            cited_from_date: datetime.datetime | None = None, cited_to_date: datetime.datetime | None = None
        ) -> None:
        self.institution = institution

         # Institution publication date range
        self.pub_from_date = pub_from_date
        self.pub_to_date = pub_to_date

        # Cited date range
        self.cited_from_date = cited_from_date
        self.cited_to_date = cited_to_date

        super().__init__()

    async def make_report(self) -> InstitutionReportWidget:
        """Make report and create the widget."""
        pub_from_date = FromDate(self.pub_from_date) if self.pub_from_date else None
        pub_to_date = ToDate(self.pub_to_date) if self.pub_to_date else None

        cited_from_date = FromDate(self.cited_from_date) if self.cited_from_date else None
        cited_to_date = ToDate(self.cited_to_date) if self.cited_to_date else None

        report = await make_institution_report(
            institution=self.institution, pub_from_date=pub_from_date, pub_to_date=pub_to_date,
            cited_from_date=cited_from_date, cited_to_date=cited_to_date
        )
        return InstitutionReportWidget(report=report)


class LoadReportWidget(Static):
    """Widget report wrapper to load data from disk."""

    class EntityType(Enum):
        """Entity reports type."""

        AUTHOR = AuthorReport
        INSTITUTION = InstitutionReport

    class EntityTypeSelector(Select[EntityType]):
        """Entity type Selector."""

    def __init__(self, entity_handler: EntityType = EntityType.AUTHOR) -> None:
        self.entity_handler = entity_handler
        super().__init__()

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

        with open(file_path, encoding="utf-8") as file:
            data = file.read()

        main_content = self.app.query_one(MainContent)
        try:
            match self.entity_handler:
                case self.EntityType.AUTHOR:
                    author_report: AuthorReport = TypeAdapter(AuthorReport).validate_json(data)
                    author_report_widget = AuthorReportWidget(report=author_report)
                    await main_content.query("*").exclude("#page-title").remove()

                    await main_content.mount(author_report_widget)
                    main_content.update_title(title=author_report.author.display_name)

                case self.EntityType.INSTITUTION:
                    institution_report: InstitutionReport = TypeAdapter(InstitutionReport).validate_json(data)
                    institution_report_widget = InstitutionReportWidget(report=institution_report)
                    await main_content.query("*").exclude("#page-title").remove()

                    await main_content.mount(institution_report_widget)
                    main_content.update_title(title=institution_report.institution.display_name)
        except ValidationError:
            self.app.notify(
                    title="Error loading report!",
                    message="The report does not have the correct structure. This may be because it is an old version or because it is not of the specified type.",  # noqa: E501
                    severity="error",
                    timeout=10.0
                )

    @on(Select.Changed)
    async def on_select_entity(self, event: Select.Changed) -> None:
        """Change entity handler."""
        match event.value:
            case self.EntityType.AUTHOR:
                self.entity_handler = self.EntityType.AUTHOR
            case self.EntityType.INSTITUTION:
                self.entity_handler = self.EntityType.INSTITUTION
            case _:
                raise NotImplementedError

    def compose(self) -> ComposeResult:
        """Compose load report widget."""
        with Horizontal(classes="filesystem-selector-container"):
            entity_options = [(name.title(), endpoint) for name, endpoint in self.EntityType.__members__.items()]

            yield FileSystemSelector(path=pathlib.Path.home(), only_dir=False, extension=[".json",])
            yield self.EntityTypeSelector(options=entity_options, value=self.entity_handler, allow_blank=False)

        with Horizontal(classes="button-container"):
            yield Button("Load Report", variant="primary", disabled=True, id="load-report-button")
