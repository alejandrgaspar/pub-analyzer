"""Report Components."""

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text
from textual import log
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, LoadingIndicator, Static, TabbedContent, TabPane

from pub_analyzer.models.author import Author
from pub_analyzer.models.report import WorkReport
from pub_analyzer.utils.report import make_report


class WorksTable(Static):
    """Full summary of all works produced by an author."""

    def __init__(self, works_reports: list[WorkReport]) -> None:
        self.works_reports = works_reports
        super().__init__()

    class _WorksTableRenderer(Static):
        def __init__(self, renderable: RenderableType, works_reports: list[WorkReport]) -> None:
            self.works_reports =works_reports
            super().__init__(renderable)

        def action_open_work_details(self, idx: int) -> None:
            """Open Modal."""
            # TODO:OPEN MODEL WITH CITATIONS INFO
            log.warning(self.works_reports[idx].work.title)

    def compose(self) -> ComposeResult:
        """Generate and handle Works Table actions."""
        first_pub_year = self.works_reports[0].work.publication_year
        last_pub_year = self.works_reports[-1].work.publication_year

        work_table = Table(title=f"Works from {first_pub_year} to {last_pub_year}", expand=True, show_lines=True)

        work_table.add_column('', justify='center', vertical='middle')
        work_table.add_column('Title', ratio=3)
        work_table.add_column('Type', ratio=2)
        work_table.add_column('Publication Date')
        work_table.add_column('Cited by count')

        for idx, work_report in enumerate(self.works_reports):
            work = work_report.work
            work_table.add_row(
                str(f"""[@click=open_work_details({idx})]{idx}[/]"""),
                Text(work.title, overflow='ellipsis'),
                work.type,
                work.publication_date,
                str(work.cited_by_count)
            )

        yield self._WorksTableRenderer(work_table, self.works_reports)


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
                    WorksTable(works_reports=report.works),
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
