"""Body components."""

from textual.app import ComposeResult
from textual.widgets import Static

from pub_analyzer.widgets.search import AuthorFinderWidget
from pub_analyzer.widgets.sidebar import SideBar


class MainContent(Static):
    """Main content Widget."""

    DEFAULT_CLASSES = "main-content"

    def __init__(self, title: str = "Title") -> None:
        self.title = title
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose dynamically the main content view."""
        yield Static(self.title, classes="title", id="page-title")
        yield AuthorFinderWidget()

class Body(Static):
    """Body App."""

    def compose(self) -> ComposeResult:
        """Body App."""
        yield SideBar()
        yield MainContent(title="Search")
