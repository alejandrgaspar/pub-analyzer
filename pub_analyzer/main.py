"""Entry Point."""

import logging
import urllib.parse
import webbrowser
from typing import ClassVar

from textual import log
from textual.app import App, ComposeResult
from textual.dom import DOMNode
from textual.logging import TextualHandler
from textual.theme import Theme
from textual.widgets import Footer

from pub_analyzer.widgets.body import Body

PUB_ANALYZER_THEME = Theme(
    name="pub-analyzer",
    primary="#004578",
    secondary="#FEA62B",
    accent="#0178D4",
    warning="#FEA62B",
    error="#B93C5B",
    success="#4EBF71",
    foreground="#1F1F1F",
    background="#EFEFEF",
    surface="#F5F5F5",
    panel="#DCE3E8",
    dark=False,
    variables={
        "boost": "#0000000A",
        "scrollbar-background": "#C7CDD2",
        "scrollbar-background-hover": "#B2B9BE",
        "scrollbar-background-active": "#9EA4A9",
        "scrollbar-corner-color": "#C7CDD2",
    },
)


class PubAnalyzerApp(App[DOMNode]):
    """Pub Analyzer App entrypoint."""

    TITLE = "Pub Analyzer"
    ENABLE_COMMAND_PALETTE = False

    CSS_PATH: ClassVar[list[str]] = [
        "css/body.tcss",
        "css/buttons.tcss",
        "css/checkbox.tcss",
        "css/collapsible.tcss",
        "css/datatable.tcss",
        "css/editor.tcss",
        "css/main.tcss",
        "css/report.tcss",
        "css/search.tcss",
        "css/summary.tcss",
        "css/tabs.tcss",
        "css/tree.tcss",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.register_theme(PUB_ANALYZER_THEME)
        self.theme = PUB_ANALYZER_THEME.name

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Body()
        yield Footer(show_command_palette=False)

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
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])

    app = PubAnalyzerApp()
    app.run()
