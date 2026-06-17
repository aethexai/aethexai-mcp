"""Call management MCP tools.

Tools: ``trigger_call``, ``get_call``, ``get_call_status``, ``list_calls``,
``batch_calls``. Each call is backed by the public Aethex API; the API enforces
auth, tenant scoping, billing health, and admission capacity server-side.
"""

from __future__ import annotations

from typing import Literal

from mcp.types import ToolAnnotations

from aethexai import AethexError
from aethexai_mcp import utils
from aethexai_mcp.client import client
from aethexai_mcp.server import mcp

CallStatus = Literal[
    "queued",
    "ringing",
    "in-progress",
    "completed",
    "failed",
    "no-answer",
    "busy",
    "canceled",
]


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True),
    description="""⚠️ COST WARNING: This tool makes an API call to Aethex which may incur costs. Only use when explicitly requested by the user.

Place an outbound call: dial `to_number` and connect the agent.

Required: `agent_id` (an agent UUID from `list_agents`) and `to_number` (the
E.164 number to dial). `from_number` is the E.164 caller ID and is required
unless the agent has an outbound SIP trunk assigned. Optional `metadata` is a
free-form object forwarded to the call trace (reserved internal keys are
rejected). The call is placed asynchronously: this returns immediately with the
Call record (`status="queued"`); poll `get_call` / `get_call_status` with the
returned `id` for terminal status. Requires the `calls:write` scope.""",
)
def trigger_call(
    agent_id: str,
    to_number: str,
    from_number: str | None = None,
    metadata: dict | None = None,
) -> dict:
    if not agent_id:
        utils.make_error("agent_id is required")
    if not to_number:
        utils.make_error("to_number is required")

    try:
        result = client.trigger_call(
            agent_id=agent_id,
            to_number=to_number,
            from_number=from_number,
            metadata=metadata or {},
        )
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Fetch a single call record by id for the caller's tenant.

`call_id` is required (the call UUID from `trigger_call` / `list_calls`).
Returns the full call record (`id`, `agent_id`, `provider`, `direction`,
`from_number`, `to_number`, `status`, `duration_seconds`, `cost_cents`,
`metadata`, timestamps), or a not-found error if no such call exists for this
tenant. Requires the `calls:read` scope.""",
)
def get_call(call_id: str) -> dict:
    if not call_id:
        utils.make_error("call_id is required")

    try:
        result = client.get_call(call_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Return lightweight telephony status for a call.

`call_id` is required (the call UUID). Returns `{status, provider, duration_s}`
where `status` is the current telephony state (e.g. `queued` / `ringing` /
`in-progress` / `completed` / `failed` / `no-answer` / `busy` / `canceled`).
Returns not-found if the call does not belong to your tenant. Requires the
`calls:read` scope.""",
)
def get_call_status(call_id: str) -> dict:
    if not call_id:
        utils.make_error("call_id is required")

    try:
        result = client.get_call_status(call_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""List the caller's tenant's calls, newest first.

Optional filters: `status` (one of `queued` / `ringing` / `in-progress` /
`completed` / `failed` / `no-answer` / `busy` / `canceled`) and `direction`
(`inbound` / `outbound`). Pagination: `limit` (default 50, capped at 1000) and
`offset` (default 0). Returns a `{data, total, offset, limit, has_more}`
envelope where each item in `data` is a full call record. Requires the
`calls:read` scope.""",
)
def list_calls(
    status: CallStatus | None = None,
    direction: Literal["inbound", "outbound"] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))

    filters: dict = {}
    if status is not None:
        filters["status"] = status
    if direction is not None:
        filters["direction"] = direction

    try:
        result = client.list_calls(offset=offset, limit=limit, **filters)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True),
    description="""⚠️ COST WARNING: This tool makes an API call to Aethex which may incur costs. Only use when explicitly requested by the user.

Dispatch a batch of outbound calls with one agent.

Required: `agent_id` (an agent UUID) and `recipients` — a non-empty list (max
10,000) of objects, each with `to_number` (E.164) and `from_number` (E.164,
required per recipient unless the agent has an outbound trunk), plus optional
per-recipient `variables`. Optional `name` / `description` label the batch.
Optional scheduling: `start_at` defers dispatch, `end_at` abandons unstarted
recipients past the deadline — both timezone-aware ISO 8601. Returns a
`batch_id` (poll batch status via the REST `GET /calls/batch/{id}`). Requires
the `calls:write` scope.""",
)
def batch_calls(
    agent_id: str,
    recipients: list[dict],
    name: str | None = None,
    description: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
) -> dict:
    if not agent_id:
        utils.make_error("agent_id is required")
    if not recipients:
        utils.make_error("recipients must be a non-empty list")

    try:
        result = client.batch_calls(
            agent_id=agent_id,
            recipients=recipients,
            name=name,
            description=description,
            start_at=start_at,
            end_at=end_at,
        )
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)
