"""Body components."""

from rich.console import RenderableType
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Static

from pub_analyzer.widgets.search import FinderWidget
from pub_analyzer.widgets.sidebar import SideBar


class MainContent(Static):
    """Main content Widget."""

    DEFAULT_CLASSES = "main-content"

    class UpdateMainContent(Message):
        """New main content required."""

        def __init__(self, new_widget: Widget, title: str | None) -> None:
            self.widget = new_widget
            self.title = title
            super().__init__()

    def __init__(self, title: str = "Title") -> None:
        self.title = title
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose dynamically the main content view."""
        yield Label(self.title, classes="title", id="page-title")
        yield FinderWidget()

    def update_title(self, title: RenderableType) -> None:
        """Update view title."""
        self.query_one("#page-title", Label).update(title)

    @on(UpdateMainContent)
    async def update_content(self, new_content: UpdateMainContent) -> None:
        """Replace the main content."""
        await self.query_children().exclude("#page-title").remove()
        if new_content.title:
            self.update_title(new_content.title)
        await self.mount(new_content.widget)


class Body(Static):
    """Body App."""

    def compose(self) -> ComposeResult:
        """Body App."""
        yield SideBar()
        yield MainContent(title="Search")
