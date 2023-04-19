"""Body components."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from pub_analyzer.widgets.search import ResearcherFinder
from pub_analyzer.widgets.sidebar import SideBar


class MainContent(Static):
    """Main content Widget."""

    DEFAULT_CLASSES = "body-containers main-content"

    def __init__(self, title: str = "Title") -> None:
        self.title = title
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose dynamically the main content view."""
        yield Vertical(
            Static(self.title, classes="title", id="page-title"),
            ResearcherFinder(),
            id="main-content-container"
        )

class Body(Static):
    """Body App."""

    def compose(self) -> ComposeResult:
        """Body App."""
        yield SideBar()
        yield MainContent(title="Search")
