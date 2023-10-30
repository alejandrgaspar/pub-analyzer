"""Custom Selector widget."""

from typing import TypeVar

from textual import on
from textual.events import Key
from textual.widgets import Select as TextualSelect

SelectType = TypeVar("SelectType")


class Select(TextualSelect[SelectType]):
    """Widget to select from a list of possible options."""

    DEFAULT_CSS = """
    /* COLORS */
    $primary-color: #b91c1c;
    $primary-color-accent: #991b1b;
    $primary-color-highlight: #dc2626;

    $bg-secondary-color: #e5e7eb;

    Select {
        height: 3;
    }

    Select:focus > SelectCurrent {
        border: tall $primary-color-accent;
    }

    Select.-expanded > SelectCurrent {
        border: tall $primary-color-accent;
    }

    SelectOverlay {
        border: tall $bg-secondary-color;
        background: $bg-secondary-color;
    }

    SelectOverlay:focus {
        border: tall $bg-secondary-color;
    }

    Select OptionList {
        background: $bg-secondary-color;
    }


    Select OptionList:focus > .option-list--option-highlighted {
        background: $primary-color;
    }

    Select OptionList > .option-list--option-hover-highlighted {
        background: $primary-color-accent;
    }

    Select OptionList:focus > .option-list--option-hover-highlighted {
        background: $primary-color-accent;
    }
    """

    @on(Key)
    def exit_focus(self, event: Key) -> None:
        """Unfocus from the input with esc KEY."""
        if event.key == "escape":
            self.screen.set_focus(None)
