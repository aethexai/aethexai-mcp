"""Usage and catalog MCP tools.

Tools: ``get_usage_summary``, ``get_daily_usage``, ``get_monthly_usage``,
``list_models``. All are read-only reads of tenant-scoped usage aggregates and
the public LLM model catalog; they incur no provider cost.
"""

from mcp.types import ToolAnnotations

from aethexai import AethexError
from aethexai_mcp import utils
from aethexai_mcp.client import client
from aethexai_mcp.server import mcp


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return aggregate usage for the caller's tenant across all resource types.

Returns a summary object: total_api_requests, total_request_duration_ms
(non-voice REST only), total_voice_seconds, total_prompt_tokens /
total_completion_tokens / total_tokens, total_audio_seconds,
total_input_characters, and a by_resource_type breakdown keyed by resource
(e.g. tts, transcription, voice_call).

Requires the usage:read scope.""",
)
def get_usage_summary() -> dict:
    try:
        return utils.to_jsonable(client.get_usage_summary())
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return a per-day usage rollup for the trailing `days` calendar days.

`days` is a date window (1..365, default 30), not a row limit: the result
always contains exactly `days` entries, one per UTC calendar day, newest-first,
with zero-filled rows for days with no activity. Each entry has date, count,
token totals, request_duration_ms, voice_seconds, audio_seconds, and
input_characters.

Requires the usage:read scope.""",
)
def get_daily_usage(days: int = 30) -> dict:
    days = max(1, min(int(days), 365))
    try:
        return utils.to_jsonable(client.get_daily_usage(days=days))
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return a per-month usage rollup for the caller's tenant, newest first.

Each entry has month, count, token totals, request_duration_ms, voice_seconds,
audio_seconds, and input_characters aggregated over that calendar month.

Requires the usage:read scope.""",
)
def get_monthly_usage() -> dict:
    try:
        return utils.to_jsonable(client.get_monthly_usage())
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return the public LLM model catalog to target in `agent.llm_model`.

Each entry has id (the public alias to pass as a model name), provider
(the model's vendor, e.g. anthropic / openai / google), and available
(whether this deployment has the upstream key needed to route the model). By
default unavailable models are hidden; pass include_unavailable=true to see
every public name regardless of deployment configuration.

Requires the models:read scope.""",
)
def list_models(include_unavailable: bool = False) -> dict:
    try:
        return utils.to_jsonable(client.list_models(include_unavailable=include_unavailable))
    except AethexError as exc:
        utils.to_error(exc)
