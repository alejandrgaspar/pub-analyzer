"""Main Report widgets."""

from textual.app import ComposeResult
from textual.widgets import LoadingIndicator, Static, TabbedContent, TabPane

from pub_analyzer.models.author import Author
from pub_analyzer.utils.report import make_report

from .author import AuthorReportPane
from .export import ExportReportPane
from .source import SourcesReportPane
from .work import WorkReportPane


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
        await container.add_pane(
            TabPane("Author", AuthorReportPane(report=report))
        )

        await container.add_pane(
            TabPane("Works", WorkReportPane(report=report))
        )

        await container.add_pane(
            TabPane("Sources", SourcesReportPane(report=report))
        )

        await container.add_pane(
            TabPane("Export", ExportReportPane(report=report))
        )

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True
