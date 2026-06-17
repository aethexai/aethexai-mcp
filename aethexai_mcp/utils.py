"""Shared helpers for the Aethex MCP server: errors, response shaping, and
file/output handling. All tool modules import the public names defined here.
"""

import base64
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import NoReturn, Union

from aethexai import AethexError
from aethexai._exceptions import APIStatusError, RateLimitError
from mcp.types import (
    BlobResourceContents,
    EmbeddedResource,
    TextContent,
    TextResourceContents,
)


class AethexMcpError(Exception):
    """Raised for tool-level failures surfaced cleanly to the MCP client."""


def make_error(text: str) -> NoReturn:
    """Raise an ``AethexMcpError`` with the given message."""
    raise AethexMcpError(text)


def to_error(exc: Exception) -> NoReturn:
    """Map an SDK exception to a clean ``AethexMcpError`` without leaking internals.

    ``APIStatusError`` subclasses carry a slug ``code`` and a human ``message``;
    we surface ``[code] message``. ``RateLimitError`` additionally appends a
    retry hint when the server provided ``retry_after``. Anything else falls
    back to ``str(exc)`` so we never expose a traceback.
    """
    if isinstance(exc, APIStatusError):
        code = exc.code or "error"
        message = exc.message or exc.__class__.__name__
        text = f"[{code}] {message}"
        if isinstance(exc, RateLimitError):
            retry_after = exc.retry_after
            if retry_after is not None:
                text += f" (retry after {retry_after} seconds)"
        make_error(text)
    if isinstance(exc, AethexError):
        make_error(str(exc) or exc.__class__.__name__)
    make_error(str(exc))


def _strip_unset(value):
    """Recursively replace SDK ``Unset`` sentinels with ``None``.

    ``Unset`` is falsy but is a real object instance, so plain truthiness checks
    would leak it into JSON. We detect it by class name to avoid importing a
    private symbol path that may shift between SDK versions.
    """
    if value is None:
        return None
    if type(value).__name__ == "Unset":
        return None
    if isinstance(value, dict):
        return {k: _strip_unset(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_strip_unset(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    return value


def to_jsonable(obj):
    """Convert an SDK response into a JSON-serializable structure for FastMCP.

    Handles, in order: ``None``; raw ``bytes`` (never returned verbatim — audio
    is saved separately, so this is a safety net that base64-encodes); the
    paginated list wrapper (real attrs ``data``/``limit``/``offset``/``total``
    plus the computed ``has_more``); attrs models exposing ``.to_dict()``;
    enums; lists/tuples; dicts; and primitives. ``Unset`` sentinels anywhere in
    the tree are flattened to ``None``.
    """
    if obj is None:
        return None
    if type(obj).__name__ == "Unset":
        return None
    # Enums (incl. str-subclass enums) before the primitive check, so the result
    # is the plain underlying value rather than an enum instance.
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    # Paginated list page: shape it explicitly with its pagination fields.
    if type(obj).__name__ == "PaginatedResponse":
        return {
            "data": [to_jsonable(item) for item in obj.data]
            if not isinstance(obj.data, type(None)) and obj.data
            else [],
            "total": _strip_unset(obj.total),
            "offset": _strip_unset(obj.offset),
            "limit": _strip_unset(obj.limit),
            "has_more": obj.has_more,
        }
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(item) for item in obj]
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return _strip_unset(to_dict())
    return _strip_unset(obj)


def is_file_writeable(path: Path) -> bool:
    """Return whether ``path`` (or its parent, if it doesn't exist) is writeable."""
    if path.exists():
        return os.access(path, os.W_OK)
    return os.access(path.parent, os.W_OK)


def make_output_file(tool: str, text: str, extension: str, full_id: bool = False) -> Path:
    """Build a timestamped output filename like ``tts_hello_20260617_101500.wav``."""
    stem = text if full_id else text[:5]
    safe_stem = stem.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"{tool}_{safe_stem}_{timestamp}.{extension}")


def make_output_path(output_directory: str | None, base_path: str | None = None) -> Path:
    """Resolve and create the directory to write outputs into.

    Absolute ``output_directory`` is used as-is; a relative one is resolved
    under ``base_path``; ``None`` falls back to ``base_path`` (default
    ``~/Desktop``).
    """
    if not base_path:
        base_path = str(Path.home() / "Desktop")

    if output_directory is None:
        output_path = Path(os.path.expanduser(base_path))
    elif os.path.isabs(output_directory):
        output_path = Path(os.path.expanduser(output_directory))
    else:
        output_path = Path(os.path.expanduser(base_path)) / Path(output_directory)

    if not is_file_writeable(output_path):
        make_error(f"Directory ({output_path}) is not writeable")
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
    ".opus",
    ".mp4",
    ".mov",
    ".webm",
}


def handle_input_file(file_path: str, audio_content_check: bool = True) -> Path:
    """Validate a user-supplied input file path and return it as a ``Path``.

    Requires an absolute path unless ``AETHEX_MCP_BASE_PATH`` is set. Verifies
    the path exists and is a regular file, and (by default) that it looks like
    an audio/video file by extension.
    """
    if not os.path.isabs(file_path) and not os.environ.get("AETHEX_MCP_BASE_PATH"):
        make_error("File path must be an absolute path if AETHEX_MCP_BASE_PATH is not set")
    path = Path(file_path)
    if not path.exists():
        make_error(f"File ({path}) does not exist")
    if not path.is_file():
        make_error(f"File ({path}) is not a file")
    if audio_content_check and path.suffix.lower() not in _AUDIO_EXTENSIONS:
        make_error(f"File ({path}) is not an audio or video file")
    return path


def get_mime_type(file_extension: str) -> str:
    """Return a MIME type for a file extension (with or without a leading dot)."""
    ext = file_extension.lstrip(".").lower()
    mime_types = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "opus": "audio/opus",
        "webm": "audio/webm",
        "txt": "text/plain",
        "json": "application/json",
        "csv": "text/csv",
        "html": "text/html",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
    }
    return mime_types.get(ext, "application/octet-stream")


def generate_resource_uri(filename: str) -> str:
    """Build an ``aethex://`` resource URI for a filename."""
    return f"aethex://{filename}"


def create_resource_response(
    file_data: bytes,
    filename: str,
    file_extension: str,
    directory: Path | None = None,
) -> EmbeddedResource:
    """Wrap raw file bytes in an MCP ``EmbeddedResource``.

    Text MIME types are embedded as decoded text when possible; everything else
    (audio, etc.) is base64-encoded as a blob. When ``directory`` is given, the
    URI carries the full on-disk path.
    """
    mime_type = get_mime_type(file_extension)
    if directory is not None:
        resource_uri = generate_resource_uri((directory / filename).as_posix())
    else:
        resource_uri = generate_resource_uri(filename)

    if mime_type.startswith("text/"):
        try:
            text_content = file_data.decode("utf-8")
            return EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=resource_uri, mimeType=mime_type, text=text_content
                ),
            )
        except UnicodeDecodeError:
            pass

    base64_data = base64.b64encode(file_data).decode("utf-8")
    return EmbeddedResource(
        type="resource",
        resource=BlobResourceContents(uri=resource_uri, mimeType=mime_type, blob=base64_data),
    )


def handle_output_mode(
    file_data: bytes,
    output_path: Path,
    filename: str,
    output_mode: str,
    success_message: str | None = None,
) -> Union[TextContent, EmbeddedResource]:
    """Return generated file data per the configured output mode.

    ``files`` saves to disk and returns a text confirmation; ``resources``
    returns an embedded resource without touching disk; ``both`` saves AND
    returns the resource.
    """
    file_extension = Path(filename).suffix.lstrip(".")
    full_file_path = output_path / filename

    if output_mode == "files":
        output_path.mkdir(parents=True, exist_ok=True)
        with open(full_file_path, "wb") as f:
            f.write(file_data)
        if success_message and "{file_path}" in success_message:
            message = success_message.replace("{file_path}", str(full_file_path))
        else:
            message = success_message or f"Success. File saved as: {full_file_path}"
        return TextContent(type="text", text=message)

    if output_mode == "resources":
        return create_resource_response(file_data, filename, file_extension, directory=output_path)

    if output_mode == "both":
        output_path.mkdir(parents=True, exist_ok=True)
        with open(full_file_path, "wb") as f:
            f.write(file_data)
        return create_resource_response(file_data, filename, file_extension, directory=output_path)

    raise ValueError(f"Invalid output mode: {output_mode}. Must be 'files', 'resources', or 'both'")


def get_output_mode_description(output_mode: str) -> str:
    """Human-readable summary of what the current output mode does, for tool docs."""
    if output_mode == "files":
        return "Saves output file to directory (default: $HOME/Desktop)"
    if output_mode == "resources":
        return "Returns output as base64-encoded MCP resource"
    if output_mode == "both":
        return (
            "Saves file to directory (default: $HOME/Desktop) "
            "AND returns as base64-encoded MCP resource"
        )
    return "Output behavior depends on AETHEX_MCP_OUTPUT_MODE setting"
