"""Sidebar components and options."""

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
