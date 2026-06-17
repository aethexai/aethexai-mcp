"""Agent CRUD tools: create, fetch, update, list, delete, and duplicate voice agents."""

import warnings
from typing import Literal

from mcp.types import ToolAnnotations
from pydantic.json_schema import PydanticJsonSchemaWarning

from aethexai import AethexError
from aethexai_mcp import utils
from aethexai_mcp.client import client
from aethexai_mcp.server import mcp

# update_agent's optional args default to the _UNSET sentinel (below) so an
# omitted field is distinguishable from an explicit JSON null. That
# non-JSON-serializable default makes pydantic emit a PydanticJsonSchemaWarning
# during FastMCP's eager schema build; the sentinel is correctly excluded from
# the published tool schema, so the warning is pure noise here — silence it.
warnings.filterwarnings("ignore", category=PydanticJsonSchemaWarning)


class _Unset:
    """Sentinel marking an ``update_agent`` argument the caller did not supply.

    A plain ``None`` default can't distinguish an omitted field from an explicit
    JSON ``null``: omitted means "leave unchanged", while ``null`` means "clear
    this nullable field". This sentinel keeps them apart — omitted args are
    dropped, explicit ``null`` is forwarded so the API clears the column.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


_UNSET = _Unset()


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""Create a voice agent for the caller's tenant.

    Required: `name` (display name), `system_prompt` (the agent's behaviour
    instructions), and `voice_id` (a voice UUID from `list_voices`; must be an
    active, model-linked voice). Common optionals: `first_message` (opener line),
    `language` ("english" or "french"), `llm_model` (a name from the model
    catalog), `dialect_style` ("formal"/"mixed"/"local"), `max_duration_seconds`,
    `temperature`, and `metadata` (free-form object). Returns the full agent
    record (`id` is the agent UUID to pass to other agent tools).

    Requires the `agents:write` scope.""",
)
def create_agent(
    name: str,
    system_prompt: str,
    voice_id: str,
    first_message: str | None = None,
    language: str | None = None,
    llm_model: str | None = None,
    dialect_style: Literal["formal", "mixed", "local"] | None = None,
    max_duration_seconds: int | None = None,
    temperature: float | None = None,
    metadata: dict | None = None,
) -> dict:
    if not name or not name.strip():
        utils.make_error("name is required")
    if not system_prompt or not system_prompt.strip():
        utils.make_error("system_prompt is required")
    if not voice_id or not voice_id.strip():
        utils.make_error("voice_id is required")

    fields: dict = {"name": name, "system_prompt": system_prompt, "voice_id": voice_id}
    if first_message is not None:
        fields["first_message"] = first_message
    if language is not None:
        fields["language"] = language
    if llm_model is not None:
        fields["llm_model"] = llm_model
    if dialect_style is not None:
        fields["dialect_style"] = dialect_style
    if max_duration_seconds is not None:
        fields["max_duration_seconds"] = max_duration_seconds
    if temperature is not None:
        fields["temperature"] = temperature
    if metadata is not None:
        fields["metadata"] = metadata

    try:
        return utils.to_jsonable(client.create_agent(**fields))
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Fetch a single agent by id for the caller's tenant.

    `agent_id` is required (the agent UUID from `create_agent` / `list_agents`).
    Returns the full agent record, or a not-found error if no such agent exists
    for this tenant.

    Requires the `agents:read` scope.""",
)
def get_agent(agent_id: str) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")
    try:
        return utils.to_jsonable(client.get_agent(agent_id))
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""Update fields on an existing agent. Only provided fields are changed.

    `agent_id` is required. Any of `name`, `system_prompt`, `voice_id`,
    `first_message`, `language`, `llm_model`, `dialect_style`,
    `max_duration_seconds`, `temperature`, or `metadata` may be supplied; omit a
    field to leave it unchanged. Passing an explicit `null` CLEARS a nullable
    field (e.g. reset `max_duration_seconds` / `temperature` to the default) —
    omitting it and clearing it are distinct. A new `voice_id` must be an active,
    model-linked voice. Returns the updated agent record.

    Requires the `agents:write` scope.""",
)
def update_agent(
    agent_id: str,
    name: str | None = _UNSET,
    system_prompt: str | None = _UNSET,
    voice_id: str | None = _UNSET,
    first_message: str | None = _UNSET,
    language: str | None = _UNSET,
    llm_model: str | None = _UNSET,
    dialect_style: Literal["formal", "mixed", "local"] | None = _UNSET,
    max_duration_seconds: int | None = _UNSET,
    temperature: float | None = _UNSET,
    metadata: dict | None = _UNSET,
) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")

    # Forward every explicitly-supplied field (including an explicit ``null`` that
    # clears a nullable column) and drop only the omitted ones.
    fields: dict = {}
    if name is not _UNSET:
        fields["name"] = name
    if system_prompt is not _UNSET:
        fields["system_prompt"] = system_prompt
    if voice_id is not _UNSET:
        fields["voice_id"] = voice_id
    if first_message is not _UNSET:
        fields["first_message"] = first_message
    if language is not _UNSET:
        fields["language"] = language
    if llm_model is not _UNSET:
        fields["llm_model"] = llm_model
    if dialect_style is not _UNSET:
        fields["dialect_style"] = dialect_style
    if max_duration_seconds is not _UNSET:
        fields["max_duration_seconds"] = max_duration_seconds
    if temperature is not _UNSET:
        fields["temperature"] = temperature
    if metadata is not _UNSET:
        fields["metadata"] = metadata

    try:
        return utils.to_jsonable(client.update_agent(agent_id, **fields))
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""List the caller's tenant's agents, newest first.

    Pagination: `limit` (default 50, capped at 1000) and `offset` (default 0).
    Returns a `{data, total, offset, limit, has_more}` envelope where each item in
    `data` is a full agent record.

    Requires the `agents:read` scope.""",
)
def list_agents(limit: int = 50, offset: int = 0) -> dict:
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))
    try:
        return utils.to_jsonable(client.list_agents(offset=offset, limit=limit))
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True),
    description="""Delete an agent by id for the caller's tenant.

    `agent_id` is required. Soft-deletes the agent and removes its knowledge
    documents (DB rows and their object-storage blobs). Returns the deletion
    result.

    Requires the `agents:write` scope.""",
)
def delete_agent(agent_id: str) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")
    try:
        return utils.to_jsonable(client.delete_agent(agent_id))
    except AethexError as exc:
        utils.to_error(exc)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""Deep-copy an agent, including its tools and knowledge base.

    `agent_id` is required (the agent UUID to copy). The new agent is named
    "<name> (copy)". Returns the full record of the new agent.

    Requires the `agents:write` scope.""",
)
def duplicate_agent(agent_id: str) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")
    try:
        return utils.to_jsonable(client.duplicate_agent(agent_id))
    except AethexError as exc:
        utils.to_error(exc)
