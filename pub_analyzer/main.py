"""Entry Point."""

import urllib.parse
import webbrowser
from typing import ClassVar

from textual import log
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.dom import DOMNode
from textual.reactive import Reactive
from textual.widgets import Footer

from pub_analyzer.widgets.body import Body
from pub_analyzer.widgets.sidebar import SideBar


class PubAnalyzerApp(App[DOMNode]):
    """Pub Analyzer App entrypoint."""

    TITLE = "Pub Analyzer"
    ENABLE_COMMAND_PALETTE = False

    CSS_PATH: ClassVar[CSSPathType | None] = [
        "css/body.tcss",
        "css/buttons.tcss",
        "css/checkbox.tcss",
        "css/collapsible.tcss",
        "css/datatable.tcss",
        "css/main.tcss",
        "css/report.tcss",
        "css/summary.tcss",
        "css/search.tcss",
        "css/tabs.tcss",
        "css/tree.tcss",
    ]
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="ctrl+d", action="toggle_dark", description="Dark mode"),
        Binding(key="ctrl+s", action="toggle_sidebar", description="Sidebar"),
    ]

    dark: Reactive[bool] = Reactive(False)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Body()
        yield Footer(show_command_palette=False)

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar."""
        self.set_focus(None)

        sidebar = self.query_one(SideBar)
        sidebar.toggle()

    def action_save_screenshot(self) -> None:
        """Take Screenshot."""
        file_path = self.app.save_screenshot()
        self.app.notify(
            title="Screenshot saved!", message=f"You can see the screenshot at {file_path}", severity="information", timeout=10.0
        )

    def action_open_link(self, link: str) -> None:
        """Open a link in the browser."""
        log.info(f"Opening link: {link}")
        if link and (link != "None"):
            webbrowser.open(urllib.parse.unquote(link))
        else:
            log.warning("Link cannot be empty!")


def run() -> None:
    """Run Pub Analyzer App."""
    app = PubAnalyzerApp()
    app.run()
