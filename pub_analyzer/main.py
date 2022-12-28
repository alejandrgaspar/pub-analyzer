"""Entry Point."""

from textual.app import App, ComposeResult
from textual.dom import DOMNode
from textual.reactive import Reactive
from textual.widgets import Footer
from widgets.body import Body


class PubAnalyzerApp(App[DOMNode]):
    """Pub Analyzer App entrypoint."""

    CSS_PATH = ["css/main.css", "css/body.css", "css/buttons.css"]
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    dark: Reactive[bool] = Reactive(False)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Body()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = PubAnalyzerApp()
    app.run()
