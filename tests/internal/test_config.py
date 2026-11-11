"""Test the user configuration from pub_analyzer/internal/config.py."""

import os
import sys
from pathlib import Path

import pytest

from pub_analyzer.internal import config
from pub_analyzer.internal.config import ConfigError, config_path, load_settings
from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR


def write_config(content: str) -> Path:
    """Write the configuration file at the location the app reads it from."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# --- Location -------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform == "win32", reason="XDG locations do not apply on Windows")
def test_config_path_follows_xdg_config_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """XDG_CONFIG_HOME relocates the configuration directory."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert config_path() == tmp_path / "pub-analyzer" / "config.toml"


@pytest.mark.skipif(sys.platform == "win32", reason="XDG locations do not apply on Windows")
@pytest.mark.parametrize("value", [None, ""], ids=["unset", "empty"])
def test_config_path_defaults_to_dot_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, value: str | None) -> None:
    """Without XDG_CONFIG_HOME the file lives in ~/.config, on macOS too."""
    if value is None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", value)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert config_path() == tmp_path / ".config" / "pub-analyzer" / "config.toml"


def test_config_path_on_windows_uses_appdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Windows keeps the file under %APPDATA%."""
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert config_path() == tmp_path / "pub-analyzer" / "config.toml"


# --- Loading --------------------------------------------------------------------------


def test_missing_file_uses_defaults() -> None:
    """Running without a configuration file is not an error."""
    assert not config_path().exists()

    assert load_settings().api_key is None


def test_api_key_is_read_from_the_file() -> None:
    """The key written in the file is the one loaded."""
    write_config('api_key = "file-key"\n')

    assert load_settings().api_key == "file-key"


@pytest.mark.parametrize("value", ["", "   "], ids=["empty", "blank"])
def test_blank_api_key_in_the_file_counts_as_none(value: str) -> None:
    """A placeholder left empty means no key."""
    write_config(f'api_key = "{value}"\n')

    assert load_settings().api_key is None


def test_environment_overrides_the_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment variable wins, so a key can be swapped for a single run."""
    write_config('api_key = "file-key"\n')
    monkeypatch.setenv(API_KEY_ENV_VAR, "env-key")

    assert load_settings().api_key == "env-key"


def test_empty_environment_variable_falls_back_to_the_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exported but empty variable does not hide the key in the file."""
    write_config('api_key = "file-key"\n')
    monkeypatch.setenv(API_KEY_ENV_VAR, "")

    assert load_settings().api_key == "file-key"


def test_unknown_keys_are_ignored() -> None:
    """A file written for a newer version still loads."""
    write_config('api_key = "file-key"\nsomething_new = 1\n')

    assert load_settings().api_key == "file-key"


def test_changes_to_the_file_apply_on_the_next_load() -> None:
    """The file is read on every load, so edits apply without restarting the app."""
    write_config('api_key = "old-key"\n')
    assert load_settings().api_key == "old-key"

    write_config('api_key = "new-key"\n')
    assert load_settings().api_key == "new-key"


# --- Errors ---------------------------------------------------------------------------


def test_invalid_toml_raises_config_error() -> None:
    """A syntax error names the file, rather than surfacing a parser traceback."""
    path = write_config("api_key = \n")

    with pytest.raises(ConfigError, match="not valid TOML") as exc_info:
        load_settings()

    assert str(path) in str(exc_info.value)


def test_wrong_type_raises_config_error_without_the_value() -> None:
    """A value of the wrong type is reported by name, never echoing what may be a secret."""
    write_config('api_key = ["secret-key"]\n')

    with pytest.raises(ConfigError, match="api_key") as exc_info:
        load_settings()

    assert "secret-key" not in str(exc_info.value)


@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="POSIX permissions, which root ignores")
def test_unreadable_file_raises_config_error() -> None:
    """A file the user cannot read is reported instead of crashing."""
    path = write_config('api_key = "file-key"\n')
    path.chmod(0)

    try:
        with pytest.raises(ConfigError, match="could not be read"):
            load_settings()
    finally:
        path.chmod(0o600)
