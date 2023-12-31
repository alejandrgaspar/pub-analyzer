"""Sidebar components and options."""
from enum import Enum

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from pub_analyzer.widgets.report.core import LoadReportWidget
from pub_analyzer.widgets.search import FinderWidget


class SideBarOptionsName(Enum):
    """List of existing Tabs titles."""

    SEARCH = "Search"
    LOAD_REPORT = "Load report"


class SideBar(Static):
    """SideBar Widget."""

    DEFAULT_CLASSES = "sidebar"

    def compose(self) -> ComposeResult:
        """Compose dynamically the sidebar options."""
        with Vertical(classes="sidebar-options-column"):
            yield Label("Menu", id="sidebar-title")

            yield Button(SideBarOptionsName.SEARCH.value, variant="primary", id="search-sidebar-button", classes="sidebar-option")
            yield Button(SideBarOptionsName.LOAD_REPORT.value, variant="primary", id="load-sidebar-button", classes="sidebar-option")

    def toggle(self) -> None:
        """Show/Hide Sidebar."""
        if self.has_class("-hidden"):
            self.remove_class("-hidden")
            self.styles.animate("width", value=20, duration=0.5)
        else:
            if self.query("*:focus"):
                self.screen.set_focus(None)
            self.styles.animate("width", value=0, duration=0.5)
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
        """Load the FinderWidget in the main view."""
        await self._replace_main_content(new_title=SideBarOptionsName.SEARCH.value, new_widget=FinderWidget())

    @on(Button.Pressed, "#load-sidebar-button")
    async def load_report(self) -> None:
        """Load the LoadReportWidget in the main view."""
        await self._replace_main_content(new_title=SideBarOptionsName.LOAD_REPORT.value, new_widget=LoadReportWidget())
