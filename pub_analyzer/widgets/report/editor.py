"""Text editor widget."""

from pydantic import BaseModel
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Label, Static, TextArea

from pub_analyzer.widgets.common import Modal


class TextEditor(Modal[str | None]):
    """Text editor widget."""

    def __init__(self, display_name: str, text: str) -> None:
        self.display_name = display_name
        self.text = text
        super().__init__()

    @on(events.Key)
    def exit_modal(self, message: events.Key) -> None:
        """Exit from the modal with esc KEY."""
        if message.key == "escape":
            self.dismiss(None)

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        """Return the edited content."""
        self.dismiss(self.query_one(TextArea).text)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        """Cancel action button handler."""
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        """Compose text editor."""
        with VerticalScroll(id="dialog"):
            yield Label(f'Editing the "{self.display_name}" field.', classes="dialog-title")

            with VerticalScroll(id="text-editor-container"):
                yield TextArea(text=self.text, theme="css", soft_wrap=True, show_line_numbers=True, tab_behavior="indent")

            with Horizontal(id="actions-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")


class EditWidget(Static):
    """Ask for edit widget."""

    def __init__(self, display_name: str, field_name: str, model: BaseModel, widget: Widget | None, widget_field: str | None) -> None:
        self.display_name = display_name
        self.field_name = field_name
        self.model = model
        self.widget = widget
        self.widget_field = widget_field
        super().__init__()

    @on(Button.Pressed)
    def launch_text_editor(self) -> None:
        """Lunch Text editor."""

        def save(new_text: str | None) -> None:
            """Save changes if save button is pressed."""
            if new_text:
                self.app.log("Value updated.")
                setattr(self.model, self.field_name, new_text)

                if self.widget and self.widget_field:
                    setattr(self.widget, self.widget_field, new_text)

        text = getattr(self.model, self.field_name)
        self.app.push_screen(TextEditor(self.display_name, text), callback=save)

    def compose(self) -> ComposeResult:
        """Compose widget."""
        with Horizontal():
            yield Button("Edit", variant="primary")
