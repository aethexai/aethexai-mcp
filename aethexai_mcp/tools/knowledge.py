"""Agent knowledge-base MCP tools.

Tools: ``upload_knowledge_doc``, ``list_knowledge_docs``,
``query_knowledge_base``, ``delete_knowledge_doc`` — manage the documents that
back an agent's retrieval-augmented (RAG) knowledge base. Reads (list, query)
require the ``agents:read`` scope; writes (upload, delete) require
``agents:write``. Every call is scoped to the API key's tenant and the given
agent, so one tenant can never reach another tenant's agent documents.
"""

from mcp.types import ToolAnnotations
from aethexai import AethexError

from aethexai_mcp.server import mcp
from aethexai_mcp.client import client
from aethexai_mcp import utils, config  # noqa: F401  (config kept for parity with sibling tool modules)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=False, openWorldHint=True),
    description="""Add a text document to an agent's knowledge base.

`agent_id` is required (the agent UUID from the agent tools). `text` is the
document body as a plain string (file uploads are not supported over MCP — paste
the extracted text). `filename` is optional and names the source (defaults to
`text_document.txt`). The text is chunked, embedded, and indexed inline, so the
returned `status` is normally `"completed"` (`"failed"` if extraction/embedding
errored). Returns the doc record (`id`, `filename`, `status`, `chunk_count`,
...).

Requires the `agents:write` scope.""",
)
def upload_knowledge_doc(agent_id: str, text: str, filename: str | None = None) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")
    if not text or not text.strip():
        utils.make_error("text content is empty")

    try:
        result = client.upload_knowledge_doc(agent_id, text=text, filename=filename)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""List the documents in an agent's knowledge base.

`agent_id` is required. Returns the document records, each with `id` (the doc
UUID to pass to `delete_knowledge_doc`), `filename`, `content_type`,
`size_bytes`, `status` (`"completed"` / `"processing"` / `"failed"`),
`chunk_count`, and `created_at`.

Requires the `agents:read` scope.""",
)
def list_knowledge_docs(agent_id: str) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")

    try:
        result = client.list_knowledge_docs(agent_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    description="""Test RAG retrieval against an agent's knowledge base.

`agent_id` and `query` (the search text) are required. `top_k` is the number of
chunks to return (default 3, capped at 20). The query is embedded and run
through hybrid search (vector similarity + keyword), then fused with RRF.
Returns the matching chunks, each with the chunk `text`, a relevance `score`,
and the `source` filename.

Requires the `agents:read` scope.""",
)
def query_knowledge_base(agent_id: str, query: str, top_k: int = 3) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")
    if not query or not query.strip():
        utils.make_error("query is required")
    query = query.strip()
    if len(query) > 4000:
        utils.make_error("query too long: max 4000 characters")
    top_k = max(1, min(int(top_k), 20))

    try:
        result = client.query_knowledge_base(agent_id, query=query, top_k=top_k)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)


@mcp.tool(
    annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True),
    description="""Delete a document from an agent's knowledge base.

`agent_id` and `doc_id` (the doc UUID from `list_knowledge_docs`) are both
required. Removes the doc, its chunks, and the stored blob.

Requires the `agents:write` scope.""",
)
def delete_knowledge_doc(agent_id: str, doc_id: str) -> dict:
    if not agent_id or not agent_id.strip():
        utils.make_error("agent_id is required")
    if not doc_id or not doc_id.strip():
        utils.make_error("doc_id is required")

    try:
        result = client.delete_knowledge_doc(agent_id, doc_id)
    except AethexError as exc:
        utils.to_error(exc)
    return utils.to_jsonable(result)
