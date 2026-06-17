"""Unit tests for ``aethexai_mcp.utils`` — the pure error/serialization/file helpers.

These exercise deterministic logic only; no network and no SDK client construction
(importing ``utils`` does not build the client), so no API key is required.
"""

from enum import Enum
from pathlib import Path

import pytest

from aethexai._exceptions import AethexError, NotFoundError, RateLimitError
from aethexai_mcp import utils
from aethexai_mcp.utils import AethexMcpError


# ── errors ──────────────────────────────────────────────────────────────────


def test_make_error_raises_aethex_mcp_error():
    with pytest.raises(AethexMcpError, match="boom"):
        utils.make_error("boom")


def test_to_error_maps_status_error_to_code_message():
    err = NotFoundError("agent missing", code="not_found", status_code=404)
    with pytest.raises(AethexMcpError, match=r"\[not_found\] agent missing"):
        utils.to_error(err)


def test_to_error_rate_limit_appends_retry_hint():
    err = RateLimitError(
        "slow down", code="rate_limited", status_code=429, headers={"Retry-After": "12"}
    )
    with pytest.raises(AethexMcpError, match=r"retry after 12.0 seconds"):
        utils.to_error(err)


def test_to_error_generic_aethex_error_falls_back_to_str():
    with pytest.raises(AethexMcpError, match="network down"):
        utils.to_error(AethexError("network down"))


def test_to_error_plain_exception_falls_back_to_str():
    with pytest.raises(AethexMcpError, match="kaboom"):
        utils.to_error(ValueError("kaboom"))


# ── to_jsonable ─────────────────────────────────────────────────────────────


class _Color(Enum):
    RED = "red"


class Unset:  # mimics the SDK sentinel (detected by class name "Unset")
    pass


class _Model:
    def to_dict(self):
        return {"a": 1, "b": Unset()}


class PaginatedResponse:  # name-detected by to_jsonable
    def __init__(self, data, total, offset, limit, has_more):
        self.data = data
        self.total = total
        self.offset = offset
        self.limit = limit
        self.has_more = has_more


def test_to_jsonable_passes_through_primitives():
    assert utils.to_jsonable("x") == "x"
    assert utils.to_jsonable(3) == 3
    assert utils.to_jsonable(None) is None


def test_to_jsonable_enum_returns_value():
    assert utils.to_jsonable(_Color.RED) == "red"


def test_to_jsonable_bytes_base64():
    assert utils.to_jsonable(b"hi") == "aGk="


def test_to_jsonable_unset_sentinel_becomes_none():
    assert utils.to_jsonable(Unset()) is None


def test_to_jsonable_strips_unset_inside_to_dict():
    assert utils.to_jsonable(_Model()) == {"a": 1, "b": None}


def test_to_jsonable_paginated_envelope():
    page = PaginatedResponse(data=[_Model()], total=1, offset=0, limit=50, has_more=False)
    out = utils.to_jsonable(page)
    assert out == {
        "data": [{"a": 1, "b": None}],
        "total": 1,
        "offset": 0,
        "limit": 50,
        "has_more": False,
    }


def test_to_jsonable_empty_paginated_data():
    page = PaginatedResponse(data=[], total=0, offset=0, limit=50, has_more=False)
    assert utils.to_jsonable(page)["data"] == []


# ── files / paths / mime / uri ──────────────────────────────────────────────


def test_make_output_file_format():
    name = utils.make_output_file("tts", "Hello world", "wav")
    assert name.name.startswith("tts_Hello_")
    assert name.suffix == ".wav"
    assert " " not in name.name


def test_make_output_file_full_id_keeps_whole_text():
    name = utils.make_output_file("preview", "abcdefgh", "wav", full_id=True)
    assert name.name.startswith("preview_abcdefgh_")


def test_make_output_path_absolute(tmp_path: Path):
    out = utils.make_output_path(str(tmp_path))
    assert out == tmp_path
    assert out.is_dir()


def test_make_output_path_relative_under_base(tmp_path: Path):
    out = utils.make_output_path("sub", base_path=str(tmp_path))
    assert out == tmp_path / "sub"
    assert out.is_dir()


def test_make_output_path_not_writeable_raises():
    with pytest.raises(AethexMcpError, match="not writeable"):
        utils.make_output_path("/this/does/not/exist/and/is/not/writeable")


def test_is_file_writeable(tmp_path: Path):
    assert utils.is_file_writeable(tmp_path) is True
    assert utils.is_file_writeable(tmp_path / "new.txt") is True


def test_get_mime_type():
    assert utils.get_mime_type("wav") == "audio/wav"
    assert utils.get_mime_type(".mp3") == "audio/mpeg"
    assert utils.get_mime_type("xyz") == "application/octet-stream"


def test_generate_resource_uri():
    assert utils.generate_resource_uri("a.wav") == "aethex://a.wav"


# ── input file validation ───────────────────────────────────────────────────


def test_handle_input_file_ok(sample_audio_file: Path):
    assert utils.handle_input_file(str(sample_audio_file)) == sample_audio_file


def test_handle_input_file_missing_raises(tmp_path: Path):
    with pytest.raises(AethexMcpError, match="does not exist"):
        utils.handle_input_file(str(tmp_path / "nope.wav"))


def test_handle_input_file_non_audio_raises(tmp_path: Path):
    doc = tmp_path / "notes.txt"
    doc.write_text("hi")
    with pytest.raises(AethexMcpError, match="not an audio"):
        utils.handle_input_file(str(doc))


def test_handle_input_file_relative_requires_base_path(monkeypatch):
    monkeypatch.delenv("AETHEX_MCP_BASE_PATH", raising=False)
    with pytest.raises(AethexMcpError, match="absolute path"):
        utils.handle_input_file("relative.wav")


# ── output mode dispatch ────────────────────────────────────────────────────


def test_handle_output_mode_files_writes_and_returns_text(tmp_path: Path):
    out = utils.handle_output_mode(b"data", tmp_path, "out.wav", "files")
    assert out.type == "text"
    assert (tmp_path / "out.wav").read_bytes() == b"data"
    assert "out.wav" in out.text


def test_handle_output_mode_resources_returns_embedded(tmp_path: Path):
    out = utils.handle_output_mode(b"data", tmp_path, "out.wav", "resources")
    assert out.type == "resource"
    assert not (tmp_path / "out.wav").exists()


def test_handle_output_mode_invalid_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="Invalid output mode"):
        utils.handle_output_mode(b"data", tmp_path, "out.wav", "bogus")


def test_get_output_mode_description():
    assert "Desktop" in utils.get_output_mode_description("files")
    assert "resource" in utils.get_output_mode_description("resources").lower()
