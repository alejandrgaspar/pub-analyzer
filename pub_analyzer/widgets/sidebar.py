"""Sidebar components and options."""
from enum import Enum

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Button, Static

from pub_analyzer.widgets.search import AuthorFinderWidget


class SideBarOptionsName(Enum):
    """List of existing Tabs titles."""

    SEARCH = "Search"


class SideBar(Static):
    """SideBar Widget."""

    DEFAULT_CLASSES = "sidebar"

    def compose(self) -> ComposeResult:
        """Compose dynamically the sidebar options."""
        yield Vertical(
            Static("Menu", id="sidebar-title"),
            Button(
                SideBarOptionsName.SEARCH.value,
                id="search-sidebar-button", variant="primary", classes="sidebar-option"
            ),
            classes="sidebar-options-column"
        )

    def toggle(self) -> None:
        """Show/Hide Sidebar."""
        if self.has_class("-hidden"):
            self.remove_class("-hidden")
        else:
            if self.query("*:focus"):
                self.screen.set_focus(None)
            self.add_class("-hidden")

    async def _replace_main_content(self, new_title: str, new_widget: Widget) -> None:
        """Delete the old widgets in the main section, update the main title and replace it with the given Widget."""
        await self.app.query("MainContent *").exclude("#page-title").remove()

        self.app.query_one("#page-title", Static).update(new_title)
        self.app.query_one("MainContent").mount(new_widget)


    @on(Button.Pressed, "#search-sidebar-button")
    async def search(self) -> None:
        """Load the AuthorFinderWidget in the main view."""
        await self._replace_main_content(new_title=SideBarOptionsName.SEARCH.value, new_widget=AuthorFinderWidget())
