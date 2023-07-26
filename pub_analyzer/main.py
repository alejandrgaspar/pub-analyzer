"""Entry Point."""

import webbrowser
from typing import ClassVar

from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.dom import DOMNode
from textual.reactive import Reactive
from textual.widgets import Footer

from pub_analyzer.widgets.body import Body
from pub_analyzer.widgets.sidebar import SideBar


class PubAnalyzerApp(App[DOMNode]):
    """Pub Analyzer App entrypoint."""

    CSS_PATH: ClassVar[CSSPathType] = [
        "css/main.css", "css/body.css", "css/buttons.css", "css/tabs.css",
        "css/search.css", "css/author.css", "css/report.css", "css/tree.css",
        "css/datatable.css"
    ]
    BINDINGS: ClassVar[list[BindingType]] = [
        ("ctrl+d", "toggle_dark", "Dark mode"),
        ("ctrl+s", "toggle_sidebar", "Sidebar"),
    ]

    dark: Reactive[bool] = Reactive(False)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Body()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar."""
        self.set_focus(None)

        sidebar = self.query_one(SideBar)
        sidebar.toggle()

    def action_open_link(self, link: str) -> None:
        """Open a link in the browser."""
        self.app.bell()
        if link:
            webbrowser.open(link)


if __name__ == "__main__":
    app = PubAnalyzerApp()
    app.run()
