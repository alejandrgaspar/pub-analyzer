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
        from pub_analyzer.widgets.body import MainContent

        main_content = self.app.query_one(MainContent)
        await main_content.query("*").exclude("#page-title").remove()
        await main_content.mount(new_widget)

        main_content.update_title(title=new_title)

    @on(Button.Pressed, "#search-sidebar-button")
    async def search(self) -> None:
        """Load the AuthorFinderWidget in the main view."""
        await self._replace_main_content(new_title=SideBarOptionsName.SEARCH.value, new_widget=AuthorFinderWidget())
