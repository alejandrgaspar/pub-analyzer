"""Works Report Widgets."""

import pathlib
import re
from urllib.parse import quote, urlparse

import httpx
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text
from textual import events, on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static, TabbedContent, TabPane

from pub_analyzer.models.author import Author
from pub_analyzer.models.report import AuthorReport, CitationReport, CitationType, InstitutionReport, WorkReport
from pub_analyzer.models.work import Location
from pub_analyzer.widgets.common import FileSystemSelector, Input, Modal, ReactiveLabel, Select
from pub_analyzer.widgets.report.cards import (
    AuthorshipCard,
    CitationMetricsCard,
    OpenAccessCard,
    OpenAccessSummaryCard,
    ReportCitationMetricsCard,
    WorksTypeSummaryCard,
)
from pub_analyzer.widgets.report.editor import EditWidget
from pub_analyzer.widgets.report.grants import AwardsTable

from .concept import ConceptsTable
from .locations import LocationsTable
from .topic import TopicsTable


class CitedByTable(Static):
    """Table with the summary of the works that cite a work."""

    DEFAULT_CSS = """
    CitedByTable .citations-table {
        height: auto;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, citations_list: list[CitationReport]) -> None:
        self.citations_list = citations_list
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose Table."""
        citations_table = Table(title="Cited By", expand=True, show_lines=True)

        # Define Columns
        citations_table.add_column("", justify="center", vertical="middle")
        citations_table.add_column("Title", ratio=3)
        citations_table.add_column("Type", ratio=2)
        citations_table.add_column("DOI")
        citations_table.add_column("Cite Type", justify="center")
        citations_table.add_column("Publication Date")
        citations_table.add_column("Cited by count")

        # Yield Rows
        for idx, cited_by_work in enumerate(self.citations_list):
            work = cited_by_work.work

            work_pdf_url = work.primary_location.pdf_url if work.primary_location else None
            title = f"""[@click=app.open_link('{quote(str(work_pdf_url))}')][u]{work.title}[/u][/]""" if work_pdf_url else work.title
            ct_value = cited_by_work.citation_type
            citation_type = f"[#909d63]{ct_value.name}[/]" if ct_value is CitationType.TypeA else f"[#bc5653]{ct_value.name}[/]"

            doi = work.ids.doi
            doi_url = f"""[@click=app.open_link('{quote(str(doi))}')]DOI[/]""" if doi else "-"

            citations_table.add_row(
                str(idx),
                Text.from_markup(title, overflow="ellipsis"),
                work.type,
                Text.from_markup(doi_url, overflow="ellipsis"),
                citation_type,
                work.publication_date,
                str(work.cited_by_count),
            )

        yield Static(citations_table, classes="citations-table")


class DownloadPane(VerticalScroll):
    """Download Work pane widget."""

    def __init__(self, work_report: WorkReport, locations: list[Location]) -> None:
        self.work_report = work_report
        self.locations = locations
        super().__init__()

    @on(FileSystemSelector.FileSelected)
    def enable_button(self, event: FileSystemSelector.FileSelected) -> None:
        """Enable button on file select."""
        if event.file_selected:
            self.query_one(Button).disabled = False
        else:
            self.query_one(Button).disabled = True

    @on(Button.Pressed, "#export-report-button")
    async def export_report(self) -> None:
        """Handle export report button."""
        export_path = self.query_one(FileSystemSelector).path_selected
        file_name = self.query_one(Input).value
        pdf_url = self.query_one(Select).value

        if export_path and file_name:
            file_path = export_path.joinpath(file_name)
            self.download_work(file_path=file_path, pdf_url=pdf_url)
            self.query_one(Button).disabled = True

    @work(exclusive=True)
    async def download_work(self, file_path: pathlib.Path, pdf_url: str) -> None:
        """Download PDF."""
        async with httpx.AsyncClient() as client:
            try:
                self.log.info(f"Starting downloading: {pdf_url}")
                response = await client.get(url=pdf_url, timeout=300, follow_redirects=True)
                response.raise_for_status()
                with open(file_path, mode="wb") as f:
                    f.write(response.content)

                self.app.notify(
                    title="PDF downloaded successfully!",
                    message=f"The file was downloaded successfully. You can go see it at [i]{file_path}[/]",
                    timeout=20.0,
                )
            except httpx.RequestError:
                self.app.notify(
                    title="Network problems!",
                    message="An error occurred while requesting. Please check your connection and try again.",
                    severity="error",
                    timeout=20.0,
                )
            except httpx.HTTPStatusError as exec:
                status_code = exec.response.status_code
                title = f"HTTP Error! Status {status_code} ({httpx.codes.get_reason_phrase(status_code)})."

                if status_code == httpx.codes.FORBIDDEN:
                    msg = (
                        "Sometimes servers forbid robots from accessing their websites."
                        + "Try to download it from your browser using the following link: "
                        + f"""[@click=app.open_link('{quote(pdf_url)}')][u]{pdf_url}[/u][/]"""
                    )
                    self.app.notify(
                        title=title,
                        message=msg,
                        severity="error",
                        timeout=30.0,
                    )
                else:
                    msg = (
                        "Try to download it from your browser using the following link: "
                        + f"""[@click=app.open_link('{quote(pdf_url)}')][u]{pdf_url}[/u][/]"""
                    )
                    self.app.notify(
                        title=title,
                        message=msg,
                        severity="error",
                        timeout=30.0,
                    )

    def safe_filename(self, title: str) -> str:
        """Create a safe filename."""
        no_tags = re.sub(r"<[^>]+>", "", title)
        hyphenated = re.sub(r"\s+", "-", no_tags.strip())
        safe = re.sub(r"[^a-zA-Z0-9\-_]", "", hyphenated)
        return safe[:20]

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        filename = self.safe_filename(self.work_report.work.title)
        suggest_file_name = f"{filename}.pdf"
        with Vertical(id="export-form"):
            with Vertical(classes="export-form-input-container"):
                yield Label("[b]Name File:[/]", classes="export-form-label")

                with Horizontal(classes="file-selector-container"):
                    options = []
                    for location in self.locations:
                        if location.source:
                            options.append((location.source.display_name, location.pdf_url))
                        else:
                            hostname = str(urlparse(location.pdf_url).hostname)
                            options.append((hostname, location.pdf_url))

                    yield Input(value=suggest_file_name, placeholder="work.pdf", classes="export-form-input")
                    yield Select(
                        options=options,
                        allow_blank=False,
                    )

            with Vertical(classes="export-form-input-container"):
                yield Label("[b]Export Directory:[/]", classes="export-form-label")
                yield FileSystemSelector(path=pathlib.Path.home(), only_dir=True)

            with Horizontal(classes="export-form-buttons"):
                yield Button("Download", variant="primary", disabled=True, id="export-report-button")


class WorkModal(Modal[None]):
    """Summary of the statistics of a work."""

    def __init__(self, work_report: WorkReport, author: Author | None) -> None:
        self.work_report = work_report
        self.author = author

        locations = self.work_report.work.locations
        self.locations_with_pdf_available = [location for location in locations if location.pdf_url]

        super().__init__()

    @on(events.Key)
    def exit_modal(self, message: events.Key) -> None:
        """Exit from the modal with esc KEY."""
        if message.key == "escape":
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        """Compose metrics and Cited by Table."""
        with VerticalScroll(id="dialog"):
            yield Label(self.work_report.work.title, classes="dialog-title")

            # Cards
            with Horizontal(classes="cards-container"):
                # Authorship's
                yield AuthorshipCard(work=self.work_report.work, author=self.author)

                # OpenAccess Info
                yield OpenAccessCard(work=self.work_report.work)

                # Citation Metrics
                yield CitationMetricsCard(work_report=self.work_report)

            with TabbedContent(id="tables-container"):
                # Abstract if exists
                if self.work_report.work.abstract:
                    with TabPane("Abstract"):
                        label = ReactiveLabel(self.work_report.work.abstract, classes="abstract")
                        yield label
                        yield EditWidget(
                            display_name="abstract",
                            field_name="abstract",
                            model=self.work_report.work,
                            widget=label,
                            widget_field="renderable",
                        )
                # Citations Table
                with TabPane("Cited By Works"):
                    if len(self.work_report.cited_by):
                        yield CitedByTable(citations_list=self.work_report.cited_by)
                    else:
                        yield Label("No works found.")
                # Concepts Table
                with TabPane("Concepts"):
                    if len(self.work_report.work.concepts):
                        yield ConceptsTable(self.work_report.work.concepts)
                    else:
                        yield Label("No Concepts found.")
                # Awards Table
                with TabPane("Awards"):
                    if len(self.work_report.work.awards):
                        yield AwardsTable(self.work_report.work.awards)
                    else:
                        yield Label("No Awards found.")
                # Locations Table
                with TabPane("Locations"):
                    if len(self.work_report.work.locations):
                        yield LocationsTable(self.work_report.work.locations)
                    else:
                        yield Label("No sources found.")
                # Topics Table
                with TabPane("Topics"):
                    if len(self.work_report.work.topics):
                        yield TopicsTable(self.work_report.work.topics)
                    else:
                        yield Label("No Topics found.")
                # Download
                location = self.work_report.work.best_oa_location
                if location and location.pdf_url:
                    with TabPane("Download"):
                        yield DownloadPane(work_report=self.work_report, locations=self.locations_with_pdf_available)


class WorksTable(Static):
    """Table with all works produced by an author."""

    DEFAULT_CSS = """
    WorksTable {
        height: auto;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, report: AuthorReport | InstitutionReport, show_empty_works: bool = True) -> None:
        self.report = report
        self.show_empty_works = show_empty_works
        super().__init__()

    class _WorksTableRenderer(Static):
        """Virtual Static Widget to handle table actions calls."""

        def __init__(self, renderable: RenderableType, report: AuthorReport | InstitutionReport) -> None:
            self.report = report
            super().__init__(renderable)

        def action_open_work_details(self, idx: int) -> None:
            """Open Modal."""
            match self.report:
                case AuthorReport():
                    self.app.push_screen(WorkModal(work_report=self.report.works[idx], author=self.report.author))
                case InstitutionReport():
                    self.app.push_screen(WorkModal(work_report=self.report.works[idx], author=None))

    def compose(self) -> ComposeResult:
        """Generate Table."""
        if self.report.works:
            first_pub_year = next((w.work.publication_year for w in self.report.works if w.work.publication_year is not None), "-")
            last_pub_year = next((w.work.publication_year for w in reversed(self.report.works) if w.work.publication_year is not None), "-")
            title = f"Works from {first_pub_year} to {last_pub_year}"
        else:
            title = "Works"

        work_table = Table(title=title, expand=True, show_lines=True)
        work_table.add_column("", justify="center", vertical="middle")
        work_table.add_column("Title", ratio=3)
        work_table.add_column("Type", ratio=2)
        work_table.add_column("DOI")
        work_table.add_column("Publication Date")
        work_table.add_column("Cited by count")

        for idx, work_report in enumerate(self.report.works):
            work = work_report.work
            if not self.show_empty_works and len(work_report.cited_by) < 1:
                continue

            doi = work.ids.doi
            doi_url = f"""[@click=app.open_link("{quote(str(doi))}")]DOI[/]""" if doi else "-"
            publication_date = work.publication_date if work.publication_date else "-"

            work_table.add_row(
                str(f"""[@click=open_work_details({idx})]{idx}[/]"""),
                Text(work.title, overflow="ellipsis"),
                Text(work.type),
                Text.from_markup(doi_url, overflow="ellipsis"),
                Text(publication_date),
                str(len(work_report.cited_by)),
            )

        yield self._WorksTableRenderer(work_table, report=self.report)


class WorkReportPane(VerticalScroll):
    """Work report Pane Widget."""

    DEFAULT_CSS = """
    WorkReportPane {
        layout: vertical;
        overflow-x: hidden;
        overflow-y: auto;
    }
    """

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
        super().__init__()

    async def toggle_empty_works(self) -> None:
        """Hide/show works if cites are cero."""
        report_works_status: bool = self.app.query_one("ReportWidget").show_empty_works  # type: ignore
        table_works_status = self.query_one(WorksTable).show_empty_works

        if self.report.works and (report_works_status != table_works_status):
            self.loading = True
            await self.query_one(WorksTable).remove()
            await self.mount(WorksTable(report=self.report, show_empty_works=report_works_status))
            self.loading = False

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        with Horizontal(classes="cards-container"):
            yield ReportCitationMetricsCard(report=self.report)
            yield WorksTypeSummaryCard(report=self.report)
            yield OpenAccessSummaryCard(report=self.report)

        if self.report.works:
            yield WorksTable(report=self.report)
