"""Conversation MCP tools.

Tools: ``list_conversations``, ``get_conversation``, ``get_transcript``,
``search_conversations``, ``submit_feedback``. Each runs scoped to the API key's
tenant and is backed by the public Aethex conversations API.
"""

from mcp.types import ToolAnnotations

from aethexai import AethexError
from aethexai_mcp import utils
from aethexai_mcp.client import client
from aethexai_mcp.server import mcp


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""List the caller's tenant's conversations, newest first.

    Each entry has `id` (pass to `get_conversation`/`get_transcript`), `call_id`,
    `agent_id`, `status`, `turn_count`, `total_duration_ms`, `transcript_text`,
    `has_recording`, `has_transcript`, and `created_at`. Paginated via `limit`
    (default 50, max 1000) and `offset`. Returns the standard
    `{data, total, offset, limit, has_more}` envelope.

    Requires the `conversations:read` scope.
    """,
)
def list_conversations(limit: int = 50, offset: int = 0) -> dict:
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))
    try:
        result = client.list_conversations(offset=offset, limit=limit)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Fetch a single conversation by id for the caller's tenant.

    `conversation_id` is required (a UUID from `list_conversations`). Returns the
    conversation's metadata: `id`, `call_id`, `agent_id`, `status`, `turn_count`,
    `total_duration_ms`, `transcript_text`, `has_recording`, `has_transcript`,
    and `created_at`. Raises not_found if the conversation does not exist for this
    tenant.

    Requires the `conversations:read` scope.
    """,
)
def get_conversation(conversation_id: str) -> dict:
    if not conversation_id or not str(conversation_id).strip():
        utils.make_error("conversation_id is required")
    try:
        result = client.get_conversation(conversation_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return the ordered turn-by-turn transcript for a conversation.

    `conversation_id` is required (a UUID from `list_conversations`). Returns
    `{"conversation_id", "turns": [...]}` where each turn has `id`, `turn_index`,
    `role` (`user`/`assistant`), `text`, per-stage latencies, `tool_calls`,
    and `created_at`. Raises not_found if the conversation does not
    exist for this tenant.

    Requires the `conversations:read` scope.
    """,
)
def get_transcript(conversation_id: str) -> dict:
    if not conversation_id or not str(conversation_id).strip():
        utils.make_error("conversation_id is required")
    try:
        result = client.get_transcript(conversation_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Full-text search across the caller's tenant's conversation turns.

    `q` is required (1-256 chars); matching is a case-insensitive substring over
    turn text. `limit` defaults to 20 (max 100). Returns
    `{"query", "results": [...], "total"}` where each result has
    `conversation_id`, `turn_id`, `text`, `role`, `turn_index`, and `created_at`.

    Requires the `conversations:read` scope.
    """,
)
def search_conversations(q: str, limit: int = 20) -> dict:
    if not q or not q.strip():
        utils.make_error("q must not be empty")
    if len(q) > 256:
        utils.make_error("q too long: max 256 characters")
    limit = max(1, min(int(limit), 100))
    try:
        result = client.search_conversations(q, limit=limit)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""Attach feedback (rating + optional comment) to a conversation.

    `conversation_id` and `rating` (an integer 1-5) are required; `comment` is
    optional free text. Feedback is stored on the conversation's metadata.
    Returns `{"success", "conversation_id", "rating"}`. Raises not_found if the
    conversation does not exist for this tenant.

    Requires the `conversations:read` scope.
    """,
)
def submit_feedback(
    conversation_id: str,
    rating: int,
    comment: str | None = None,
) -> dict:
    if not conversation_id or not str(conversation_id).strip():
        utils.make_error("conversation_id is required")
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        utils.make_error("rating must be an integer between 1 and 5")
    fields: dict = {"rating": rating}
    if comment is not None:
        fields["comment"] = comment
    try:
        result = client.submit_feedback(conversation_id, **fields)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)
