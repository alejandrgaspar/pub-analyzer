"""Input widgets."""

import re
from collections.abc import Iterable

from rich.highlighter import Highlighter
from textual import on
from textual.events import Key
from textual.suggester import Suggester
from textual.validation import Regex, Validator
from textual.widgets import Input as TextualInput


class Input(TextualInput):
    """Input with extra bindings."""

    DEFAULT_CSS = """
    /* COLORS */
    $primary-color: #b91c1c;
    $primary-color-accent: #991b1b;
    $primary-color-highlight: #dc2626;

    Input {
        border: tall $background;
    }

    Input:focus {
        border: tall $primary-color-accent;
    }
    Input.-invalid {
        border: tall orange 40%;
    }
    Input.-invalid:focus {
        border: tall orange 60%;
    }
    """

    @on(Key)
    def exit_focus(self, event: Key) -> None:
        """Unfocus from the input with esc KEY."""
        if event.key == "escape":
            self.screen.set_focus(None)


class DateSuggester(Suggester):
    """Suggest date format."""

    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion as of the current input date."""
        if match := re.match(r"^(?P<year>\d{1,4})(-|$)(?P<month>\d{1,2})?(-|$)(?P<day>\d{1,2})?$", value):
            date_comp = match.groupdict()

            year = date_comp["year"] or "yyyy"
            month = date_comp["month"] or "mm"
            day = date_comp["day"] or "dd"

            return f"{year}-{month}-{day}"
        return None


class DateInput(Input):
    """Input with Date validation."""

    def __init__(
        self,
        value: str | None = None,
        placeholder: str = "",
        highlighter: Highlighter | None = None,
        password: bool = False,
        *,
        validators: Validator | Iterable[Validator] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        suggester = DateSuggester()

        super().__init__(
            value,
            placeholder,
            highlighter,
            password,
            suggester=suggester,
            validators=validators,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

        self.validators.append(
            Regex(
                regex=r"^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$", failure_description="Input must be formatted as `yyyy-mm-dd`"
            )
        )
