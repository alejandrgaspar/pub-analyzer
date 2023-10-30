"""Filters selectors for OpenAlex API."""

from datetime import datetime

from rich.console import RenderableType
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive, var
from textual.widgets import Checkbox, Static

from .input import DateInput


class Filter(Static):
    """Base filter."""

    class Changed(Message):
        """Posted when any input in the filter changes."""

    filter_disabled: reactive[bool] = reactive(True)
    """Is filter inputs disabled?"""

    @property
    def validation_state(self) -> bool:
        """Return true if all valitadtion passes."""
        raise NotImplementedError


class DateRangeFilter(Filter):
    """Date range selector."""

    DEFAULT_CSS = """
    DateRangeFilter {
        height: auto;
        layout: horizontal;
    }

    DateRangeFilter Checkbox {
        width: 1fr;
    }

    DateRangeFilter .filter-inputs {
        height: auto;
        width: 3fr;
    }

    DateRangeFilter DateInput {
        width: 1fr;
    }
    """

    from_date: var[datetime | None] = var(None)
    to_date: var[datetime | None] = var(None)

    def __init__(
            self, checkbox_label: str = "Date Range", renderable: RenderableType = "", *, expand: bool = False, shrink: bool = False,
            markup: bool = True, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False
        ) -> None:
        self.checkbox_label = checkbox_label
        super().__init__(renderable, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes, disabled=disabled)

    def compose(self) -> ComposeResult:
        """Compose Date range selector."""
        yield Checkbox(self.checkbox_label, value=False, id="filter-checkbox")
        with Horizontal(classes="filter-inputs", disabled=True):
            yield DateInput(placeholder="From yyyy-mm-dd", id="from-date")
            yield DateInput(placeholder="To yyyy-mm-dd", id="to-date")

    def watch_filter_disabled(self, is_filter_disabled: bool) -> None:
        """Toggle filter disable status with the reactive attribute."""
        self.query_one(".filter-inputs", Horizontal).disabled = is_filter_disabled

    @property
    def validation_state(self) -> bool:
        """Return true if all datetime inputs are correctly formatted."""
        return all([self.from_date, self.to_date])

    @on(Checkbox.Changed)
    def toggle_filter_disabled(self, event: Checkbox.Changed) -> None:
        """Toggle filter enabled status."""
        event.stop()
        self.post_message(self.Changed())
        self.filter_disabled = not event.value

    @on(DateInput.Changed)
    def date_input_handler(self, event: DateInput.Changed) -> None:
        """Handle date input change."""
        event.stop()
        self.post_message(self.Changed())
        date_input = event.input

        if event.validation_result:
            new_value = datetime.strptime(event.value, "%Y-%m-%d") if event.validation_result.is_valid else None
        else:
            new_value = None

        if date_input.id == "from-date":
            self.from_date = new_value
        elif date_input.id == "to-date":
            self.to_date = new_value
