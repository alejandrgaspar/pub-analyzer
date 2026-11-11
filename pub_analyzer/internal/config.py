"""User configuration, read from a TOML file and the environment.

Every setting is looked up in this order, the first one found winning:

1. An environment variable named after the setting with a `PUB_ANALYZER_` prefix,
   e.g. `PUB_ANALYZER_API_KEY`.
2. The configuration file returned by `config_path`, e.g.
   `~/.config/pub-analyzer/config.toml`.
3. The default declared on `Settings`.

Example:
    ```toml
    # ~/.config/pub-analyzer/config.toml
    api_key = "your-key"
    ```
"""

import os
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import tomli_w
from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

APP_NAME = "pub-analyzer"
"""Name of the directory holding the configuration file."""

CONFIG_FILE_NAME = "config.toml"
"""Name of the configuration file."""

ENV_PREFIX = "PUB_ANALYZER_"
"""Prefix of the environment variables overriding the configuration file."""


class ConfigError(Exception):
    """The configuration file exists but cannot be used."""


def config_dir() -> Path:
    r"""Locate the directory holding the configuration file.

    Returns:
        `%APPDATA%\pub-analyzer` on Windows. Everywhere else, including macOS,
        `$XDG_CONFIG_HOME/pub-analyzer`, falling back to `~/.config/pub-analyzer`.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"

    return Path(base) / APP_NAME


def config_path() -> Path:
    """Locate the configuration file.

    Returns:
        Path of the configuration file, which may not exist.
    """
    return config_dir() / CONFIG_FILE_NAME


class Settings(BaseSettings):
    """User settings, layered from the environment over the configuration file."""

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, env_ignore_empty=True, extra="ignore")

    api_key: str | None = None
    """OpenAlex API key, from https://openalex.org/settings/api."""

    @field_validator("api_key")
    @classmethod
    def _blank_means_unset(cls, value: str | None) -> str | None:
        """Treat an empty or whitespace only key as no key at all."""
        if value is None:
            return None

        return value.strip() or None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Read the environment first, then the configuration file.

        Info:
            The file location is resolved on every load rather than once at import, so it
            follows the environment it is read from.
        """
        return init_settings, env_settings, TomlConfigSettingsSource(settings_cls, toml_file=config_path())


def load_settings() -> Settings:
    """Load the user settings.

    Returns:
        Settings, with defaults for anything the user did not configure.

    Raises:
        ConfigError: The configuration file exists but cannot be read, is not valid
            TOML, or holds a value of the wrong type.

    Info:
        The file is read again on every call, so edits apply without restarting the app.
    """
    path = config_path()

    try:
        return Settings()
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise _read_error(path, exc) from exc
    except ValidationError as exc:
        # Built from the error locations only: the offending value may be a secret.
        problems = "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors())
        raise ConfigError(f"The configuration file {path} has invalid values. {problems}") from exc


def read_stored_api_key() -> str | None:
    """Read the API key saved in the configuration file, ignoring the environment.

    Returns:
        The saved key, or `None` when the file does not exist or holds no key.

    Raises:
        ConfigError: The configuration file exists but cannot be read or is not valid TOML.
    """
    api_key = _read_config_file(config_path()).get("api_key")
    if not isinstance(api_key, str):
        return None

    return api_key.strip() or None


def save_api_key(api_key: str | None) -> Path:
    """Save the API key in the configuration file, keeping every other setting in it.

    Args:
        api_key: Key to save. An empty or `None` key removes it from the file instead.

    Returns:
        Path of the configuration file.

    Raises:
        ConfigError: The existing file cannot be read or is not valid TOML, in which case
            it is left untouched, or the new file cannot be written.

    Info:
        Like any TOML writer, this drops the comments of a hand edited file.
    """
    path = config_path()
    settings = _read_config_file(path)

    api_key = (api_key or "").strip()
    if api_key:
        settings["api_key"] = api_key
    else:
        settings.pop("api_key", None)

    _write_config_file(path, settings)

    return path


def _read_error(path: Path, exc: OSError | tomllib.TOMLDecodeError) -> ConfigError:
    """Explain why the configuration file could not be read."""
    if isinstance(exc, OSError):
        return ConfigError(f"The configuration file {path} could not be read: {exc.strerror}")

    return ConfigError(f"The configuration file {path} is not valid TOML: {exc}")


def _read_config_file(path: Path) -> dict[str, Any]:
    """Read the configuration file as written, without the environment or any default.

    Args:
        path: Configuration file.

    Returns:
        Its settings, or none at all when the file does not exist.

    Raises:
        ConfigError: The file exists but cannot be read or is not valid TOML.
    """
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except FileNotFoundError:
        return {}
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise _read_error(path, exc) from exc


def _write_config_file(path: Path, settings: dict[str, Any]) -> None:
    """Replace the configuration file with the given settings.

    Args:
        path: Configuration file, created along with its directory when missing.
        settings: Every setting the file holds.

    Raises:
        ConfigError: The file cannot be written.

    Info:
        The settings are written to a temporary file which then replaces the old one, so a
        crash never leaves a half written file. That file is readable by its owner only,
        since it holds the API key. A symlinked file, as dotfile managers create, is
        written through rather than replaced by a regular file.
    """
    target = path.resolve()

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as file:
                tomli_w.dump(settings, file)
            os.replace(temp_name, target)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
    except OSError as exc:
        raise ConfigError(f"The configuration file {path} could not be written: {exc.strerror}") from exc
