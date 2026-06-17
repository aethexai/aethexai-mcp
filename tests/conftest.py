"""Shared pytest fixtures for the aethexai-mcp test suite."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_audio_file(tmp_path: Path) -> Path:
    """A small file with an audio extension (content is not validated)."""
    path = tmp_path / "sample.wav"
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    return path
