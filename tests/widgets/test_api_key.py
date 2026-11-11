"""Test configuring the OpenAlex API key from the sidebar."""

import tomllib

import pytest
from textual.pilot import Pilot
from textual.widgets import Button

from pub_analyzer.internal.config import ConfigError, config_path, load_settings
from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR
from pub_analyzer.main import PubAnalyzerApp
from pub_analyzer.widgets import settings
from pub_analyzer.widgets.common import Input
from pub_analyzer.widgets.settings import ApiKeyModal
from tests.widgets.helpers import click_when_ready, spy_on_notifications, wait_until


def write_config(content: str) -> None:
    """Write the configuration file the app reads."""
    config_path().parent.mkdir(parents=True, exist_ok=True)
    config_path().write_text(content)


async def open_dialog(pilot: Pilot) -> ApiKeyModal:
    """Click the sidebar's API key button, and return the dialog it opens."""
    assert await pilot.click("#api-key-sidebar-button")
    await wait_until(pilot, lambda: isinstance(pilot.app.screen, ApiKeyModal))

    dialog = pilot.app.screen
    assert isinstance(dialog, ApiKeyModal)
    return dialog


@pytest.mark.asyncio
async def test_dialog_shows_the_saved_key_masked() -> None:
    """The input starts with the key in the file, hidden like a password, and focused for typing."""
    write_config('api_key = "saved-key"\n')

    async with PubAnalyzerApp().run_test() as pilot:
        dialog = await open_dialog(pilot)
        api_key_input = dialog.query_one(Input)

        assert api_key_input.value == "saved-key"
        assert api_key_input.password
        assert api_key_input.has_focus


@pytest.mark.asyncio
async def test_the_key_can_be_shown_and_hidden() -> None:
    """The toggle reveals the key to check it and hides it again, leaving the input ready to save."""
    write_config('api_key = "saved-key"\n')
    app = PubAnalyzerApp()

    async with app.run_test() as pilot:
        dialog = await open_dialog(pilot)
        api_key_input = dialog.query_one(Input)
        toggle = dialog.query_one("#toggle-visibility", Button)

        await click_when_ready(pilot, toggle)
        await pilot.pause()
        assert not api_key_input.password
        assert str(toggle.label) == "Hide"
        assert api_key_input.has_focus

        await click_when_ready(pilot, toggle)
        await pilot.pause()
        assert api_key_input.password
        assert str(toggle.label) == "Show"
        assert api_key_input.has_focus

        # With the focus back on the input, typing and enter carry on as before.
        await pilot.press(*"-new", "enter")
        await wait_until(pilot, lambda: not isinstance(app.screen, ApiKeyModal))

    assert load_settings().api_key == "saved-key-new"


@pytest.mark.asyncio
async def test_saving_writes_the_key_and_closes_the_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typed key lands in the configuration file, which the next report reads."""
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test() as pilot:
        await open_dialog(pilot)
        await pilot.press(*"new-key")
        assert await pilot.click("#save")
        await wait_until(pilot, lambda: not isinstance(app.screen, ApiKeyModal))

    assert load_settings().api_key == "new-key"
    notify.assert_called_once()
    assert notify.call_args.kwargs["title"] == "API key saved!"
    assert "new-key" not in notify.call_args.kwargs["message"]


@pytest.mark.asyncio
async def test_enter_saves_the_key() -> None:
    """Pressing enter in the input saves, as pasting a key and hitting enter is the natural flow."""
    app = PubAnalyzerApp()

    async with app.run_test() as pilot:
        await open_dialog(pilot)
        await pilot.press(*"new-key", "enter")
        await wait_until(pilot, lambda: not isinstance(app.screen, ApiKeyModal))

    assert load_settings().api_key == "new-key"


@pytest.mark.asyncio
async def test_saving_an_empty_input_removes_the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clearing the input and saving removes the key from the file."""
    write_config('api_key = "saved-key"\n')
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test() as pilot:
        dialog = await open_dialog(pilot)
        dialog.query_one(Input).value = ""
        assert await pilot.click("#save")
        await wait_until(pilot, lambda: not isinstance(app.screen, ApiKeyModal))

    assert tomllib.loads(config_path().read_text()) == {}
    assert notify.call_args.kwargs["title"] == "API key removed!"


@pytest.mark.asyncio
@pytest.mark.parametrize("close", ["cancel", "escape"])
async def test_closing_without_saving_keeps_the_file(close: str) -> None:
    """Cancel and escape throw away what was typed."""
    write_config('api_key = "saved-key"\n')
    app = PubAnalyzerApp()

    async with app.run_test() as pilot:
        await open_dialog(pilot)
        await pilot.press(*"-changed")

        if close == "cancel":
            assert await pilot.click("#cancel")
        else:
            await pilot.press("escape")
        await wait_until(pilot, lambda: not isinstance(app.screen, ApiKeyModal))

    assert config_path().read_text() == 'api_key = "saved-key"\n'


@pytest.mark.asyncio
async def test_a_failed_save_keeps_the_dialog_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the file cannot be written, the error is shown and the typed key is not lost."""

    def fail(api_key: str | None) -> None:
        raise ConfigError("The configuration file could not be written: Permission denied")

    monkeypatch.setattr(settings, "save_api_key", fail)
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test() as pilot:
        dialog = await open_dialog(pilot)
        await pilot.press(*"new-key")
        assert await pilot.click("#save")
        await pilot.pause()

        assert app.screen is dialog
        assert dialog.query_one(Input).value == "new-key"

    notify.assert_called_once()
    assert notify.call_args.kwargs["severity"] == "error"
    assert "Permission denied" in notify.call_args.kwargs["message"]


@pytest.mark.asyncio
async def test_a_broken_file_is_reported_instead_of_opening_the_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    """Saving would overwrite a file the user has to fix by hand, so the dialog stays closed."""
    write_config("api_key = \n")
    app = PubAnalyzerApp()
    notify = spy_on_notifications(app, monkeypatch)

    async with app.run_test() as pilot:
        assert await pilot.click("#api-key-sidebar-button")
        await pilot.pause()

        assert not isinstance(app.screen, ApiKeyModal)

    notify.assert_called_once()
    assert notify.call_args.kwargs["severity"] == "error"
    assert str(config_path()) in notify.call_args.kwargs["message"]


@pytest.mark.asyncio
@pytest.mark.parametrize(("env_value", "warned"), [("env-key", True), ("", False)], ids=["set", "empty"])
async def test_dialog_warns_when_the_environment_overrides_the_file(monkeypatch: pytest.MonkeyPatch, env_value: str, warned: bool) -> None:
    """A key saved here would be ignored while the environment variable is set, so the dialog says so."""
    monkeypatch.setenv(API_KEY_ENV_VAR, env_value)

    async with PubAnalyzerApp().run_test() as pilot:
        dialog = await open_dialog(pilot)

        assert len(dialog.query(".dialog-warning")) == (1 if warned else 0)
