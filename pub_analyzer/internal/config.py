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
import tomllib
from pathlib import Path

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
    except OSError as exc:
        raise ConfigError(f"The configuration file {path} could not be read: {exc.strerror}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"The configuration file {path} is not valid TOML: {exc}") from exc
    except ValidationError as exc:
        # Built from the error locations only: the offending value may be a secret.
        problems = "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors())
        raise ConfigError(f"The configuration file {path} has invalid values. {problems}") from exc
