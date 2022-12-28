"""Body components."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static


class SideBar(Static):
    """SideBar Widget."""

    DEFAULT_CLASSES = "body-containers sidebar"

    def compose(self) -> ComposeResult:
        """Compose dynamically the sidebar options."""
        yield Vertical(
            Static("Menu", classes="menu-title"),
            *[
                Button(f"Section {number}", variant="primary", classes="menu-option")
                for number in range(5)
            ],
            classes="options-column"
        )


class MainContent(Static):
    """Main content Widget."""

    DEFAULT_CLASSES = "body-containers main-content"

    def __init__(self, title: str = "Title") -> None:
        self.title = title
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose dynamically the main content view."""
        yield Vertical(
            Static(self.title, classes="title"),
        )


class Body(Static):
    """Body App."""

    def compose(self) -> ComposeResult:
        """Body App."""
        yield SideBar()
        yield MainContent()
