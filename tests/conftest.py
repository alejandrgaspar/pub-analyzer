"""Fixtures configuration."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Specifying the async backend to run on."""
    return "asyncio"
