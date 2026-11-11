"""Fixtures shared by the widget tests."""

from pathlib import Path

import pytest


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the home directory, where the file pickers start, at an empty temporary directory.

    This keeps tests from listing or writing to the real home directory.
    """
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return tmp_path
