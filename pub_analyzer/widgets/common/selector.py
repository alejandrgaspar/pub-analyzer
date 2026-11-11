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

    Select > SelectCurrent {
        border: tall transparent;
        background: $boost;
        color: $text;

        Static#label {
            color: $text-disabled;
        }

        &.-has-value Static#label {
            color: $text;
        }

        .arrow {
            color: $text-muted;
        }
    }

    Select:focus > SelectCurrent {
        border: tall $primary-color-accent;
        background-tint: transparent;
    }

    Select.-expanded > SelectCurrent {
        border: tall $primary-color-accent;
    }

    Select > SelectOverlay {
        border: tall $background;
        background: $bg-secondary-color;
        color: $text;
    }

    Select > SelectOverlay:focus {
        border: tall $background;
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
