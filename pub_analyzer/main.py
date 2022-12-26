"""Entry Point."""

from textual.app import App, ComposeResult
from textual.dom import DOMNode
from textual.widgets import Footer, Header


class PubAnalyzerApp(App[DOMNode]):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = PubAnalyzerApp()
    app.run()
