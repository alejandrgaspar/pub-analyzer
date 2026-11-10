"""Verify HTTPX2 cassette recording, playback and API key filtering."""

from pathlib import Path
from typing import Any

import httpx2 as httpx
import pytest
import vcr
from vcr.errors import CannotOverwriteExistingCassetteException


@pytest.mark.asyncio
async def test_cassette_filters_keys_and_replays_without_network(tmp_path: Path, vcr_config: dict[str, Any]) -> None:
    """Recording strips the key; playback matches another key and rejects unknown requests."""
    cassette_path = tmp_path / "recording.yaml"
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    recorder = vcr.VCR(**vcr_config)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with recorder.use_cassette(str(cassette_path), record_mode="all"):
            response = await client.get("https://api.openalex.org/works?filter=x&api_key=recording-secret")
            assert response.json() == {"ok": True}

        assert len(requests) == 1
        assert "recording-secret" not in cassette_path.read_text()
        assert "api_key" not in cassette_path.read_text()

        with recorder.use_cassette(str(cassette_path), record_mode="none"):
            response = await client.get("https://api.openalex.org/works?filter=x&api_key=another-secret")
            assert response.json() == {"ok": True}
            with pytest.raises(CannotOverwriteExistingCassetteException):
                await client.get("https://api.openalex.org/works?filter=unknown")

        assert len(requests) == 1
