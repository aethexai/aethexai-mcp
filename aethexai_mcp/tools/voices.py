"""Voice catalog and text-to-speech MCP tools.

Tools: ``list_voices``, ``synthesize_speech``, ``preview_voice``,
``list_tag_vocabulary``. Each calls the public Aethex API via the SDK ``client``;
tenant scoping, auth, rate limiting, and billing are enforced server-side.
"""

from typing import Literal, Union

from mcp.types import EmbeddedResource, TextContent, ToolAnnotations

from aethexai import AethexError

from aethexai_mcp import config, utils
from aethexai_mcp.client import client
from aethexai_mcp.server import mcp

_PREVIEW_DEFAULT_TEXT = "Hello, this is a sample of my voice."


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""List available Aethex TTS voices for the caller's tenant.

    Returns the global catalog plus any voices cloned on this tenant. Each entry
    has `id` (the voice UUID to pass to `synthesize_speech`/`preview_voice`),
    `name`, `language`, `gender`, `tags`, `country`, and a `preview_url`.
    Optional filters: `language` (lowercase), `tag` (a token from
    `list_tag_vocabulary`), and `supports_dialect_style`. Off-vocabulary filter
    values return an empty list.

    Requires the `voices:read` scope.

    Args:
        language: Filter by language (lowercase, e.g. "english" or "french").
        supports_dialect_style: Filter to voices that support dialect/style control.
        tag: Filter by a single tag token from `list_tag_vocabulary`.
        limit: Maximum number of voices to return (default 100).
        offset: Number of voices to skip for pagination (default 0).
    """,
)
def list_voices(
    language: str | None = None,
    supports_dialect_style: bool | None = None,
    tag: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    try:
        result = client.list_voices(
            language=language,
            supports_dialect_style=supports_dialect_style,
            tag=tag,
            limit=limit,
            offset=offset,
        )
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description=f"""⚠️ COST WARNING: This tool makes an API call to Aethex which may incur costs. Only use when explicitly requested by the user.

    Generate speech audio from text using an Aethex voice. {utils.get_output_mode_description(config.OUTPUT_MODE)}.

    Produces a complete WAV container (PCM16, mono). `text` is capped (see the
    platform's TTS character limit); split longer scripts into multiple calls.
    `voice_id` is a voice UUID from `list_voices` (omit for the tenant's default
    voice). `language` is a lowercase string ("english" or "french").

    Requires the `tts:use` scope.

    Args:
        text: The text to convert to speech.
        voice_id: Voice UUID from `list_voices` (omit for the default voice).
        language: Voice language, lowercase ("english" or "french").
        output_directory: Directory where files should be saved (only used when
            saving files). Defaults to $HOME/Desktop if not provided.

    Returns:
        Text content with the saved file path or an MCP resource with audio data,
        depending on the configured output mode.
    """,
)
def synthesize_speech(
    text: str,
    voice_id: str | None = None,
    language: Literal["english", "french"] = "english",
    output_directory: str | None = None,
) -> Union[TextContent, EmbeddedResource]:
    if not text.strip():
        utils.make_error("text must not be empty")

    fields: dict = {"text": text, "language": language}
    if voice_id is not None:
        fields["voice_id"] = voice_id
    try:
        audio = client.synthesize_speech(**fields)
    except AethexError as exc:
        utils.to_error(exc)

    output_path = utils.make_output_path(output_directory, config.BASE_PATH)
    filename = utils.make_output_file("tts", text, "wav")
    return utils.handle_output_mode(audio, output_path, filename, config.OUTPUT_MODE)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description=f"""⚠️ COST WARNING: This tool makes an API call to Aethex which may incur costs. Only use when explicitly requested by the user.

    Synthesize a short sample clip for a specific voice. {utils.get_output_mode_description(config.OUTPUT_MODE)}.

    `voice_id` is required (a UUID from `list_voices`); `text` is optional and
    capped at 300 characters. Returns a WAV clip like `synthesize_speech`.

    Requires the `tts:use` scope.

    Args:
        voice_id: Voice UUID from `list_voices`.
        text: Sample text to synthesize (optional, capped at 300 characters).
        output_directory: Directory where files should be saved (only used when
            saving files). Defaults to $HOME/Desktop if not provided.

    Returns:
        Text content with the saved file path or an MCP resource with audio data,
        depending on the configured output mode.
    """,
)
def preview_voice(
    voice_id: str,
    text: str = _PREVIEW_DEFAULT_TEXT,
    output_directory: str | None = None,
) -> Union[TextContent, EmbeddedResource]:
    if not voice_id.strip():
        utils.make_error("voice_id must not be empty")

    try:
        audio = client.preview_voice(voice_id=voice_id, text=text or _PREVIEW_DEFAULT_TEXT)
    except AethexError as exc:
        utils.to_error(exc)

    output_path = utils.make_output_path(output_directory, config.BASE_PATH)
    filename = utils.make_output_file("preview", voice_id, "wav")
    return utils.handle_output_mode(audio, output_path, filename, config.OUTPUT_MODE)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return the closed voice-tag vocabulary, grouped into four buckets.

    Buckets are `tone` / `voice_texture` / `delivery_style` / `business_persona`.
    Any single token from any bucket is a valid `tag` filter on `list_voices`.

    Requires the `voices:read` scope.
    """,
)
def list_tag_vocabulary() -> dict:
    try:
        result = client.list_tag_vocabulary()
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)
