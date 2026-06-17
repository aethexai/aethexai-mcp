"""Transcription MCP tools.

Tools: ``transcribe_audio`` (sync), ``submit_transcription_job`` (async),
``get_transcription_job``, ``cancel_transcription_job``.

Each tool calls the public Aethex API via the SDK; auth, tenant scoping, rate
limits, admission, billing, and upload validation are all enforced server-side.
The two upload tools read a local audio file and send it as a multipart body.
"""

import io

from mcp.types import ToolAnnotations

from aethexai import AethexError
from aethexai._generated.models.body_transcribe_async_api_v1_transcribe_async_post import (
    BodyTranscribeAsyncApiV1TranscribeAsyncPost,
)
from aethexai._generated.models.body_transcribe_sync_api_v1_transcribe_post import (
    BodyTranscribeSyncApiV1TranscribePost,
)
from aethexai._generated.types import File

from aethexai_mcp import utils
from aethexai_mcp.client import client
from aethexai_mcp.server import mcp


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""⚠️ COST WARNING: This tool makes an API call to Aethex which may incur costs. Only use when explicitly requested by the user.

    Transcribe an audio file synchronously and return the text.

    ``input_file_path`` is the path to the audio file to transcribe (required;
    WAV, FLAC, or OGG/Opus, capped by the platform's upload size + duration
    limits). ``language`` is an optional lowercase hint ("english" / "french");
    omit it to let the recognizer decide.

    Returns the transcript record: ``{id, text, language, duration_seconds,
    segments, status, processing_time_ms, created_at}``.

    Requires the ``transcribe:use`` scope.
    """,
)
def transcribe_audio(
    input_file_path: str,
    language: str | None = None,
) -> dict:
    path = utils.handle_input_file(input_file_path)
    with path.open("rb") as fh:
        data = fh.read()
    mime_type = utils.get_mime_type(path.suffix)
    body = BodyTranscribeSyncApiV1TranscribePost(
        file=File(payload=io.BytesIO(data), file_name=path.name, mime_type=mime_type),
        language=language,
    )
    try:
        result = client.transcribe_audio(body=body)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""⚠️ COST WARNING: This tool makes an API call to Aethex which may incur costs. Only use when explicitly requested by the user.

    Submit an audio file for asynchronous transcription.

    Stores the audio and enqueues a background job, returning immediately with a
    job record whose ``status`` is "pending". ``input_file_path`` is the path to
    the audio file (required; same format/size/duration limits as
    ``transcribe_audio``). ``language`` is an optional lowercase hint.

    Poll ``get_transcription_job`` with the returned ``id`` to fetch the result,
    or cancel it with ``cancel_transcription_job`` while it is still pending.

    Note: completion webhooks are not delivered over MCP — the tool surface is
    poll-only. Poll ``get_transcription_job`` for the result.

    Requires the ``transcribe:use`` scope.
    """,
)
def submit_transcription_job(
    input_file_path: str,
    language: str | None = None,
) -> dict:
    path = utils.handle_input_file(input_file_path)
    with path.open("rb") as fh:
        data = fh.read()
    mime_type = utils.get_mime_type(path.suffix)
    body = BodyTranscribeAsyncApiV1TranscribeAsyncPost(
        file=File(payload=io.BytesIO(data), file_name=path.name, mime_type=mime_type),
        language=language,
    )
    try:
        result = client.transcribe_audio_async(body=body)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Fetch the status and result of an asynchronous transcription job.

    ``job_id`` is the ``id`` returned by ``submit_transcription_job``. Returns the
    job record: ``status`` (pending/queued/retrying/completed/failed/cancelled),
    the transcribed ``text`` once complete, plus ``language``,
    ``duration_seconds``, ``processing_time_ms``, ``error_message``, and
    webhook-delivery fields. Returns not-found if the job does not belong to your
    tenant.

    Requires the ``transcribe:use`` scope.
    """,
)
def get_transcription_job(job_id: str) -> dict:
    try:
        result = client.get_transcription_job(job_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True),
    description="""Cancel a queued asynchronous transcription job.

    ``job_id`` is the ``id`` returned by ``submit_transcription_job``. Only jobs
    that are still pending, queued, or retrying can be cancelled; cancelling a job
    that is already running or completed returns a conflict.

    Requires the ``transcribe:use`` scope.
    """,
)
def cancel_transcription_job(job_id: str) -> dict:
    try:
        result = client.cancel_transcription_job(job_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)
