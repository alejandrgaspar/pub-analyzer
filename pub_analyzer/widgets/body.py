"""Body components."""

from rich.console import RenderableType
from textual.app import ComposeResult
from textual.widgets import Label, Static

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
        yield Label(self.title, classes="title", id="page-title")
        yield AuthorFinderWidget()

    def update_title(self, title: RenderableType) -> None:
        """Update view title."""
        self.query_one("#page-title", Label).update(title)


class Body(Static):
    """Body App."""

    def compose(self) -> ComposeResult:
        """Body App."""
        yield SideBar()
        yield MainContent(title="Search")
