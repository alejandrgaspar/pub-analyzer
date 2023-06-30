"""Report Components."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import LoadingIndicator, Pretty, Static

from pub_analyzer.models.author import Author
from pub_analyzer.utils.report import make_report


class ReportWidget(Static):
    """Report generator view."""

    def __init__(self, author: Author, works_api_url: str) -> None:
        self.works_api_url = works_api_url
        self.author = author

        super().__init__()

    def compose(self) -> ComposeResult:
        """Create main info container and showing a loading animation."""
        yield LoadingIndicator()
        yield VerticalScroll(id="main-container")

    def on_mount(self) -> None:
        """Hiding the empty container and calling the data in the background."""
        self.query_one("#main-container", VerticalScroll).display = False
        self.run_worker(self.make_report(), exclusive=True)

    async def make_report(self) -> None:
        """Generate the report and compose the widget."""
        report = await make_report(author=self.author)
        container = self.query_one("#main-container", VerticalScroll)

        await container.mount(
            Pretty(report)
        )

        # Show results
        self.query_one(LoadingIndicator).display = False
        container.display = True
