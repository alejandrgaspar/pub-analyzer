"""Sidebar components and options."""

from enum import Enum
from importlib.metadata import version

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from pub_analyzer.internal.config import ConfigError, read_stored_api_key
from pub_analyzer.widgets.report.core import LoadReportWidget
from pub_analyzer.widgets.search import FinderWidget
from pub_analyzer.widgets.settings import ApiKeyModal


class SideBarOptionsName(Enum):
    """List of existing Tabs titles."""

    SEARCH = "Search"
    LOAD_REPORT = "Load report"


class SideBar(Static):
    """SideBar Widget."""

    DEFAULT_CLASSES = "sidebar"

    def compose(self) -> ComposeResult:
        """Compose dynamically the sidebar options."""
        pub_analyzer_version = version("pub-analyzer")

        with Vertical(classes="sidebar-options-column"):
            yield Label("Menu", id="sidebar-title")

            with Vertical(classes="sidebar-buttons-column"):
                yield Button(SideBarOptionsName.SEARCH.value, variant="primary", id="search-sidebar-button", classes="sidebar-option")
                yield Button(SideBarOptionsName.LOAD_REPORT.value, variant="primary", id="load-sidebar-button", classes="sidebar-option")

            yield Button("API key", id="api-key-sidebar-button")
            yield Label(f"v{pub_analyzer_version}", id="module-version-label")

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

    @on(Button.Pressed, "#api-key-sidebar-button")
    def configure_api_key(self) -> None:
        """Open the dialog saving the OpenAlex API key, filled with the saved one."""
        try:
            api_key = read_stored_api_key()
        except ConfigError as exc:
            self.app.notify(title="Error reading the configuration!", message=str(exc), severity="error", timeout=20.0, markup=False)
            return

        self.app.push_screen(ApiKeyModal(api_key=api_key))
