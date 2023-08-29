"""Works Report Widgets."""

from urllib.parse import quote

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Label, Static, TabbedContent, TabPane

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
        citations_table = Table(title='Cited By', expand=True, show_lines=True)

        # Define Columns
        citations_table.add_column('', justify='center', vertical='middle')
        citations_table.add_column('Title', ratio=3)
        citations_table.add_column('Type', ratio=2)
        citations_table.add_column('DOI')
        citations_table.add_column('Cite Type', justify='center')
        citations_table.add_column('Publication Date')
        citations_table.add_column('Cited by count')

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
                Text.from_markup(title, overflow='ellipsis'),
                work.type,
                Text.from_markup(doi_url, overflow='ellipsis'),
                citation_type,
                work.publication_date,
                str(work.cited_by_count)
            )

        yield Static(citations_table, classes='citations-table')


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
                # Abtract if exists
                if self.work_report.work.abstract:
                    with TabPane("Abstract"):
                        yield Label(self.work_report.work.abstract, classes="abstract")


class WorksTable(Static):
    """Table with all works produced by an author."""

    DEFAULT_CSS = """
    WorksTable {
        height: auto;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, report: AuthorReport | InstitutionReport) -> None:
        self.report = report
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
            first_pub_year = self.report.works[0].work.publication_year
            last_pub_year = self.report.works[-1].work.publication_year
            title = f"Works from {first_pub_year} to {last_pub_year}"
        else:
            title = "Works"

        work_table = Table(title=title, expand=True, show_lines=True)
        work_table.add_column('', justify='center', vertical='middle')
        work_table.add_column('Title', ratio=3)
        work_table.add_column('Type', ratio=2)
        work_table.add_column('DOI')
        work_table.add_column('Publication Date')
        work_table.add_column('Cited by count')

        for idx, work_report in enumerate(self.report.works):
            work = work_report.work
            doi = work.ids.doi
            doi_url = f"""[@click=app.open_link("{quote(str(doi))}")]DOI[/]""" if doi else "-"

            work_table.add_row(
                str(f"""[@click=open_work_details({idx})]{idx}[/]"""),
                Text(work.title, overflow='ellipsis'),
                Text(work.type),
                Text.from_markup(doi_url, overflow='ellipsis'),
                Text(work.publication_date),
                str(work.cited_by_count)
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

    def compose(self) -> ComposeResult:
        """Compose content pane."""
        with Horizontal(classes="cards-container"):
            yield ReportCitationMetricsCard(report=self.report)
            yield WorksTypeResumeCard(report=self.report)
            yield OpenAccessResumeCard(report=self.report)

        if self.report.works:
            yield WorksTable(report=self.report)
