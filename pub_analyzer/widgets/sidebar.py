"""Sidebar components and options."""
from enum import Enum

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static

from pub_analyzer.widgets.search import ResearcherFinder


class SideBarOptionsName(Enum):
    """List of existing Tabs titles."""

    SEARCH = "Search"


class SideBar(Static):
    """SideBar Widget."""

    DEFAULT_CLASSES = "body-containers sidebar"

    def compose(self) -> ComposeResult:
        """Compose dynamically the sidebar options."""
        yield Vertical(
            Static("Menu", classes="menu-title"),
            Button(
                SideBarOptionsName.SEARCH.value,
                id="search-sidebar-button", variant="primary", classes="menu-option"
            ),
            classes="options-column"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Remove old widgets in the main section, evaluate what button from the sidebar was pressed and redirect."""
        main_content_container = self.app.query_one("#main-content-container")
        page_title = self.app.query_one("#page-title", Static)

        old_widgets = self.app.query("MainContent Vertical *").exclude("#page-title")
        await old_widgets.remove()

        if event.button.id == "search-sidebar-button":
            main_content_container.mount(ResearcherFinder())
            page_title.renderable = SideBarOptionsName.SEARCH.value
