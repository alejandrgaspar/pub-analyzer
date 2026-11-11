"""Shared pytest configuration."""

import os
from typing import Any

import pytest

from pub_analyzer.internal.openalex.client import API_KEY_ENV_VAR, API_KEY_PARAM

# Textual's test pilot waits for running animations on every pause, click and key press,
# and the app's CSS animates every color change for 500ms. Textual reads this when it
# is first imported, so it must be set before any test module imports it.
os.environ["TEXTUAL_ANIMATIONS"] = "none"


@pytest.fixture
def vcr_config() -> dict[str, Any]:
    """Configure VCR for every cassette backed test.

    Danger:
        `filter_query_parameters` is what keeps the OpenAlex API key out of the recorded
        cassettes, which are committed to the repository. Removing it would write the key
        of whoever runs `make test-record` into version control.

    Info:
        VCR applies this filter both when recording and when matching a request against a
        cassette, so recordings stay key free and playback works whether or not the
        developer running the tests has a key configured.
    """
    return {"filter_query_parameters": [API_KEY_PARAM]}


@pytest.fixture(autouse=True)
def _unset_api_key(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory) -> None:
    """Keep a developer's own API key out of the tests.

    The client falls back to the environment and the configuration file when no key is
    passed explicitly, so a key set in the shell or in `~/.config/pub-analyzer/config.toml`
    would otherwise change what the tests observe. The configuration directory is pointed
    at an empty temporary directory, where tests may write a file of their own.

    Recording is the exception: OpenAlex refuses unauthenticated calls, so `make
    test-record` needs the real key to reach the API. The `vcr_config` filter above is
    what stops that key from reaching the cassettes.
    """
    if request.config.getoption("--record-mode", default=None) not in (None, "none"):
        return

    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    config_home = tmp_path_factory.mktemp("config")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("APPDATA", str(config_home))
