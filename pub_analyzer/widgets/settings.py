"""Settings dialogs."""

import os
from pathlib import Path
from urllib.parse import quote

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label

from pub_analyzer.internal.config import ConfigError, config_path, save_api_key
from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR, API_KEY_SETTINGS_URL
from pub_analyzer.widgets.common import Input, Modal


def _display_path(path: Path) -> str:
    """Shorten a path inside the home directory to start with `~`, as users write it."""
    try:
        return str(Path("~") / path.relative_to(Path.home()))
    except ValueError:
        return str(path)


class ApiKeyModal(Modal[None]):
    """Dialog saving the OpenAlex API key to the configuration file."""

    DEFAULT_CSS = """
    $text-primary-color: black;
    $warning-text-color: #b45309;

    ApiKeyModal #dialog {
        width: 90;
        max-width: 100%;
        height: auto;
        margin: 0 2;
        padding: 0 2;
    }

    ApiKeyModal .dialog-text {
        width: 100%;
        margin: 0 1 1 1;
    }

    ApiKeyModal #api-key-row {
        height: auto;
    }

    ApiKeyModal #api-key-input {
        width: 1fr;
    }

    ApiKeyModal #toggle-visibility {
        width: 10;
        min-width: 10;
        margin-left: 1;
    }

    ApiKeyModal .dialog-hint {
        width: 100%;
        margin: 1 1 0 1;
        color: $text-primary-color 50%;
    }

    ApiKeyModal .dialog-warning {
        width: 100%;
        margin: 1 1 0 1;
        color: $warning-text-color;
    }

    ApiKeyModal #actions-buttons {
        height: 3;
        margin: 1 0;
        align: center middle;

        Button {
            margin: 0 2;
        }
    }
    """

    def __init__(self, api_key: str | None) -> None:
        """Create the dialog.

        Args:
            api_key: Key currently saved in the configuration file, shown masked.
        """
        self.api_key = api_key
        super().__init__()

    @on(events.Key)
    def exit_modal(self, message: events.Key) -> None:
        """Exit from the modal with esc KEY."""
        if message.key == "escape":
            self.dismiss(None)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        """Close without saving."""
        self.dismiss(None)

    @on(Button.Pressed, "#toggle-visibility")
    def toggle_visibility(self, event: Button.Pressed) -> None:
        """Show or hide the key.

        Focus goes back to the input, so typing and pressing enter to save keep working.
        """
        api_key_input = self.query_one(Input)
        api_key_input.password = not api_key_input.password
        event.button.label = "Show" if api_key_input.password else "Hide"
        api_key_input.focus()

    @on(Button.Pressed, "#save")
    @on(Input.Submitted)
    def save(self) -> None:
        """Save the key, or remove it when the input is empty, and close the dialog.

        The dialog stays open when the file cannot be written, so the key is not lost.
        """
        api_key = self.query_one(Input).value

        try:
            path = save_api_key(api_key)
        except ConfigError as exc:
            self.app.notify(title="Error saving the API key!", message=str(exc), severity="error", timeout=20.0, markup=False)
            return

        if api_key.strip():
            message, title = f"Saved to {_display_path(path)}", "API key saved!"
        else:
            message, title = f"Removed from {_display_path(path)}", "API key removed!"

        self.app.notify(title=title, message=message, severity="information", timeout=10.0, markup=False)

        self.dismiss(None)

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Vertical(id="dialog"):
            yield Label("OpenAlex API key", classes="dialog-title")
            yield Label(
                "OpenAlex requires an API key to build reports. Get a free one at:"
                f" [@click=app.open_link('{quote(API_KEY_SETTINGS_URL)}')]{API_KEY_SETTINGS_URL}[/].",
                classes="dialog-text",
            )

            with Horizontal(id="api-key-row"):
                yield Input(value=self.api_key or "", placeholder="Paste your API key", password=True, id="api-key-input")
                yield Button("Show", id="toggle-visibility")

            yield Label(f"Saved to {_display_path(config_path())}. Leave it empty to remove the key.", classes="dialog-hint", markup=False)
            if os.environ.get(API_KEY_ENV_VAR, "").strip():
                yield Label(
                    f"{API_KEY_ENV_VAR} is set in your environment, and takes precedence over the key saved here.",
                    classes="dialog-warning",
                    markup=False,
                )

            with Horizontal(id="actions-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")
