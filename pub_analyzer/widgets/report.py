"""Report Components."""

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Label, LoadingIndicator, Static, TabbedContent, TabPane

from pub_analyzer.models.author import Author
from pub_analyzer.models.report import CitationType, Report, WorkReport
from pub_analyzer.utils.report import make_report


class WorkResume(Screen[None]):
    """Summary of the statistics of a work."""

    def __init__(self, work_report: WorkReport, author: Author) -> None:
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
                with Vertical(classes='card'):
                    yield Label('[italic]Authorships[/italic]', classes='card-title')

                    with VerticalScroll(classes='card-author-container'):
                        for authorship in self.work_report.work.authorships:
                            if authorship.author.display_name == self.author.display_name:
                                author_name_formated = f'[b #909d63]{authorship.author.display_name}[/]'
                            else:
                                author_name_formated = str(authorship.author.display_name)

                            yield Label(f'- [b]{authorship.author_position}:[/b] {author_name_formated}')

                # OpenAccess Info
                with Vertical(classes='card'):
                    yield Label('[italic]Open Access[/italic]', classes='card-title')

                    yield Label(f'[bold]Status:[/bold] {self.work_report.work.open_access.oa_status}')

                    work_url = self.work_report.work.open_access.oa_url
                    if work_url:
                        yield Label(f"""[bold]URL:[/bold] [@click="app.open_link('{work_url}')"]{work_url}[/]""")

                # Citation Metrics
                with Vertical(classes='card'):
                    yield Label('[italic]Citation[/italic]', classes='card-title')

                    yield Label(f'[bold]Count:[/bold] {self.work_report.work.cited_by_count}')
                    yield Label(f'[bold]Type A:[/bold] {self.work_report.citation_resume.type_a_count}')
                    yield Label(f'[bold]Type B:[/bold] {self.work_report.citation_resume.type_b_count}')

            # Citations Table
            citations_table = Table(title='Cited By', expand=True, show_lines=True)

            citations_table.add_column('', justify='center', vertical='middle')
            citations_table.add_column('Title', ratio=3)
            citations_table.add_column('Type', ratio=2)
            citations_table.add_column('Cite Type', justify='center')
            citations_table.add_column('Publication Date')
            citations_table.add_column('Cited by count')

            for idx, cited_by_work in enumerate(self.work_report.cited_by):
                work = cited_by_work.work

                work_pdf_url = work.primary_location.pdf_url
                title = f"""[@click="app.open_link('{work_pdf_url}')"][u]{work.title}[/u][/]""" if work_pdf_url else work.title  # noqa: E501
                ct_value = cited_by_work.citation_type
                citation_type = f"[#909d63]{ct_value.name}[/]" if ct_value is CitationType.TypeA else f"[#bc5653]{ct_value.name}[/]"  # noqa: E501

                citations_table.add_row(
                    str(idx),
                    Text.from_markup(title, overflow='ellipsis'),
                    work.type,
                    citation_type,
                    work.publication_date,
                    str(work.cited_by_count)
                )

            if citations_table.row_count > 0:
                yield Static(citations_table, id='citations-table')


class WorksTable(Static):
    """Full summary of all works produced by an author."""

    def __init__(self, report: Report) -> None:
        self.report = report
        super().__init__()

    class _WorksTableRenderer(Static):
        def __init__(self, renderable: RenderableType, report: Report) -> None:
            self.report = report
            super().__init__(renderable)

        def action_open_work_details(self, idx: int) -> None:
            """Open Modal."""
            self.app.push_screen(WorkResume(work_report=self.report.works[idx], author=self.report.author))

    def compose(self) -> ComposeResult:
        """Generate and handle Works Table actions."""
        first_pub_year = self.report.works[0].work.publication_year
        last_pub_year = self.report.works[-1].work.publication_year

        work_table = Table(title=f"Works from {first_pub_year} to {last_pub_year}", expand=True, show_lines=True)

        work_table.add_column('', justify='center', vertical='middle')
        work_table.add_column('Title', ratio=3)
        work_table.add_column('Type', ratio=2)
        work_table.add_column('Publication Date')
        work_table.add_column('Cited by count')

        for idx, work_report in enumerate(self.report.works):
            work = work_report.work
            work_table.add_row(
                str(f"""[@click=open_work_details({idx})]{idx}[/]"""),
                Text(work.title, overflow='ellipsis'),
                work.type,
                work.publication_date,
                str(work.cited_by_count)
            )

        yield self._WorksTableRenderer(work_table, report=self.report)


class ReportWidget(Static):
    """Report generator view."""

    def __init__(self, author: Author, works_api_url: str) -> None:
        self.works_api_url = works_api_url
        self.author = author

        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and showing a loading animation."""
        yield LoadingIndicator()
        yield TabbedContent(id="main-container")

    def on_mount(self) -> None:
        """Hiding the empty container and calling the data in the background."""
        self.query_one("#main-container", TabbedContent).display = False
        self.run_worker(self.make_report(), exclusive=True)

    async def make_report(self) -> None:
        """Generate the report and compose the widget."""
        report = await make_report(author=self.author)
        container = self.query_one("#main-container", TabbedContent)

        # Compose Report
        #TODO:Author.
        await container.add_pane(
            TabPane(
                "Author",
                VerticalScroll(
                    Label("TODO1"),
                    classes="block-container"
                ),
            )
        )

        #TODO:Works.
        await container.add_pane(
            TabPane(
                "Works",
                VerticalScroll(
                    Label("Works"),
                    WorksTable(report=report),
                    classes="block-container"
                ),
            )
        )

        #TODO:Locations.
        await container.add_pane(
            TabPane(
                "Locations",
                VerticalScroll(
                    Label("TODO3"),
                    classes="block-container"
                ),
            )
        )

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True
