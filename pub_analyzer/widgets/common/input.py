"""Input widgets."""

from textual import on
from textual.events import Key
from textual.widgets import Input as TextualInput


class Input(TextualInput):
    """Input with extra bindings."""

    DEFAULT_CSS = """
    /* COLORS */
    $primary-color: #b91c1c;
    $primary-color-accent: #991b1b;
    $primary-color-highlight: #dc2626;

    Input {
        border: tall $primary-color-accent;
    }

    Input:focus {
        border: tall $primary-color-highlight;
    }
    """

    @on(Key)
    def exit_focus(self, event: Key) -> None:
        """Unfocus from the input with esc KEY."""
        if event.key == 'escape':
            self.screen.set_focus(None)
