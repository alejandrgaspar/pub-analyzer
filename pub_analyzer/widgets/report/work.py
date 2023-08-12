"""Works Report Widgets."""

import math
from urllib.parse import quote

from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import DataTable, Label, Static, TabbedContent, TabPane

from pub_analyzer.models.author import Author
from pub_analyzer.models.report import AuthorReport, CitationReport, CitationType, InstitutionReport, WorkReport
from pub_analyzer.widgets.common import Modal
from pub_analyzer.widgets.report.cards import (
    AuthorshipCard,
    CitationMetricsCard,
    OpenAccessCard,
    OpenAccessResumeCard,
    ReportCitationMetricsCard,
    WorksTypeResumeCard,
)

from .locations import LocationsTable


class CitedByTable(Static):
    """Table with the summary of the works that cite a work."""

    DEFAULT_CSS = """
    CitedByTable DataTable #cited-by-table {
        height: auto;
    }
    """

    def __init__(self, citations_list: list[CitationReport]) -> None:
        self.citations_list = citations_list
        super().__init__()

    @on(DataTable.RowHighlighted)
    async def focus_row(self, message: DataTable.RowHighlighted) -> None:
        """Focus row."""
        citations_table: DataTable[Text] = self.app.query_one("#cited-by-table", DataTable)
        citations_table.get_row(message.row_key)

    def compose(self) -> ComposeResult:
        """Compose table."""
        yield DataTable(zebra_stripes=True, header_height=2, id="cited-by-table")


    def on_mount(self) -> None:
        """Generate table."""
        title_width = 95

        citations_table: DataTable[Text] = self.app.query_one("#cited-by-table", DataTable)
        citations_table.cursor_type = "row"

        # Define Columns
        citations_table.add_column('Title', width=title_width)
        citations_table.add_column('Type', width=20)
        citations_table.add_column('DOI', width=5)
        citations_table.add_column('Cite Type', width=12)
        citations_table.add_column('Publication Date')
        citations_table.add_column('Cited by count')

        # Yield Rows
        for idx, cited_by_work in enumerate(self.citations_list, start=1):
            work = cited_by_work.work

            work_pdf_url = work.primary_location.pdf_url if work.primary_location else None
            title = f"""[@click=app.open_link('{quote(str(work_pdf_url))}')][u]{work.title}[/u][/]""" if work_pdf_url else work.title
            ct_value = cited_by_work.citation_type
            citation_type = f"[#909d63]{ct_value.name}[/]" if ct_value is CitationType.TypeA else f"[#bc5653]{ct_value.name}[/]"

            doi = work.ids.doi
            doi_url = f"""[u][@click=app.open_link('{quote(str(doi))}')]DOI[/][/u]""" if doi else "-"

            row_height = math.ceil(len(work.title) / title_width) + 1
            citations_table.add_row(
                Text.from_markup(title, overflow='ellipsis'),
                Text(work.type),
                Text.from_markup(doi_url, overflow='ellipsis'),
                Text.from_markup(citation_type),
                Text(work.publication_date),
                Text(str(work.cited_by_count)),
                height=row_height,
                label=Text.from_markup(f"{idx}", justify="center")
            )


class WorkModal(Modal[None]):
    """Summary of the statistics of a work."""

    def __init__(self, work_report: WorkReport, author: Author | None) -> None:
        self.work_report = work_report
        self.author = author
        super().__init__()

    @on(events.Key)
    def exit_modal(self, message: events.Key) -> None:
        """Exit from the modal with esc KEY."""
        if message.key == 'escape':
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        """Compose metrics and Cited by Table."""
        with VerticalScroll(id='dialog'):
            yield Label(self.work_report.work.title, classes='dialog-title')

            # Cards
            with Horizontal(classes='cards-container'):
                # Authorships
                yield AuthorshipCard(work=self.work_report.work, author=self.author)

                # OpenAccess Info
                yield OpenAccessCard(work=self.work_report.work)

                # Citation Metrics
                yield CitationMetricsCard(work_report=self.work_report)


            with TabbedContent(id="tables-container"):
                # Citations Table
                with TabPane("Cited By Works"):
                    if len(self.work_report.cited_by):
                        yield CitedByTable(citations_list=self.work_report.cited_by)
                    else:
                        yield Label("No works found.")
                # Locations Table
                with TabPane("Locations"):
                    if len(self.work_report.work.locations):
                        yield LocationsTable(self.work_report.work.locations)
                    else:
                        yield Label("No sources found.")


class WorksTable(Static):
    """Table with all works produced by an author."""

    DEFAULT_CSS = """
    WorksTable DataTable {
        height: auto;
    }
    """

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
        super().__init__()

    @on(DataTable.RowLabelSelected)
    async def open_work_details(self, message: DataTable.RowLabelSelected) -> None:
        """Open work deatils in a modal."""
        match self.report:
            case AuthorReport():
                await self.app.push_screen(WorkModal(work_report=self.report.works[message.row_index], author=self.report.author))
            case InstitutionReport():
                await self.app.push_screen(WorkModal(work_report=self.report.works[message.row_index], author=None))

    def compose(self) -> ComposeResult:
        """Compose table."""
        first_pub_year = self.report.works[0].work.publication_year
        last_pub_year = self.report.works[-1].work.publication_year

        yield Label(f"Works from {first_pub_year} to {last_pub_year}", classes="table-title")
        yield DataTable(zebra_stripes=True, header_height=2)


    def on_mount(self) -> None:
        """Generate Table."""
        title_width = 100

        work_table: DataTable[Text] = self.query_one(DataTable)
        work_table.cursor_type = "row"

        work_table.add_column('Title', width=title_width)
        work_table.add_column('Type', width=20)
        work_table.add_column('DOI', width=5)
        work_table.add_column('Publication Date', width=20)
        work_table.add_column('Cited by count', width=14)

        for idx, work_report in enumerate(self.report.works, start=1):
            work = work_report.work
            doi = work.ids.doi
            doi_url = f"""[u][@click=app.open_link("{quote(str(doi))}")]DOI[/][/u]""" if doi else "-"

            row_height = math.ceil(len(work.title) / title_width) + 1
            work_table.add_row(
                Text(work.title, overflow='ellipsis'),
                Text(work.type),
                Text.from_markup(doi_url, overflow='ellipsis'),
                Text(work.publication_date),
                Text(str(work.cited_by_count)),
                height=row_height,
                label=Text.from_markup(f"""[u]{idx}[/u]""", justify="center")
            )


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

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        with Horizontal(classes="cards-container"):
            yield ReportCitationMetricsCard(report=self.report)
            yield WorksTypeResumeCard(report=self.report)
            yield OpenAccessResumeCard(report=self.report)

        yield WorksTable(report=self.report)
