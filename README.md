<p align="center">
  <img src="https://raw.githubusercontent.com/aethexai/aethexai-mcp/main/.github/assets/aethex-mcp-banner.png" alt="Aethex MCP Server" width="100%">
</p>

<h1 align="center">Aethex MCP Server</h1>

<p align="center">
  <b>Drive the Aethex voice platform from any MCP client.</b><br>
  Synthesize speech, transcribe audio, build voice agents and their knowledge bases,<br>
  place calls, browse conversations, and read usage, from Claude, Cursor, Codex, and more.
</p>

<p align="center">
  <a href="https://pypi.org/project/aethexai-mcp/"><img alt="PyPI" src="https://img.shields.io/pypi/v/aethexai-mcp?style=flat-square&logo=pypi&logoColor=white&label=pypi&labelColor=0B0E14&color=38BDF8&cacheSeconds=300"></a>
  <a href="https://pypi.org/project/aethexai-mcp/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/aethexai-mcp?style=flat-square&logo=python&logoColor=white&labelColor=0B0E14&color=1E293B"></a>
  <a href="https://github.com/aethexai/aethexai-mcp/actions/workflows/test.yml"><img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/aethexai/aethexai-mcp/test.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white&label=tests&labelColor=0B0E14&color=22D3EE"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-64748B?style=flat-square&labelColor=0B0E14"></a>
</p>

<p align="center">
  <a href="https://developers.aethexai.com/docs"><b>Documentation</b></a> &nbsp;·&nbsp;
  <a href="https://developers.aethexai.com/dashboard">Dashboard</a> &nbsp;·&nbsp;
  <a href="https://developers.aethexai.com/docs/api-reference">API Reference</a> &nbsp;·&nbsp;
  <a href="https://discord.gg/ccyuJNZm7x">Discord</a> &nbsp;·&nbsp;
  <a href="mailto:developers@aethexai.com">Support</a>
</p>

<br>

| 🎙️ Voice agents | 🗣️ Text-to-speech | ✍️ Transcription | 📞 Calls & conversations |
|:--|:--|:--|:--|
| Build, configure, ground in knowledge | Synthesize & preview to WAV | Sync & async jobs | Place calls, search transcripts, read usage |

The [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) server for the
[Aethex](https://aethexai.com) voice-AI platform. It wraps the public Aethex API through the
[`aethexai`](https://pypi.org/project/aethexai) Python SDK and exposes it as MCP tools, so clients
like Claude Desktop, Claude Code, Cursor, Windsurf, and Codex can run voice workflows directly.
Authentication is one variable, `AETHEX_API_KEY`; every tool runs scoped to that key's tenant.

## Install

Run it with [uv](https://github.com/astral-sh/uv); your MCP client launches it on demand, with no install step:

```bash
uvx aethexai-mcp
```

Or install it into an environment:

```bash
pip install aethexai-mcp
```

Requires Python 3.11+. Get an `AETHEX_API_KEY` from the [developer portal](https://developers.aethexai.com).

## Quickstart

Add the server to Claude Desktop under **Settings > Developer > Edit Config** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "Aethex": {
      "command": "uvx",
      "args": ["aethexai-mcp"],
      "env": { "AETHEX_API_KEY": "ae_live_..." }
    }
  }
}
```

Restart Claude and ask it to "list my Aethex voices". On Windows, enable **Help > Enable Developer Mode** first.

## MCP clients

Any MCP client works. Common setups:

| Client | Setup |
|---|---|
| **Claude Desktop** | Add the JSON block above to `claude_desktop_config.json`. |
| **Claude Code** | `claude mcp add aethex --env AETHEX_API_KEY=ae_live_... -- uvx aethexai-mcp` |
| **Codex** | Add an `[mcp_servers.aethex]` table to `~/.codex/config.toml` (below). |
| **Cursor / Windsurf** | `pip install aethexai-mcp`, then run `python -m aethexai_mcp --api-key=ae_live_... --print` and paste the printed block into the client's MCP config. |

Codex (`~/.codex/config.toml`):

```toml
[mcp_servers.aethex]
command = "uvx"
args = ["aethexai-mcp"]
env = { AETHEX_API_KEY = "ae_live_..." }
```

To override the API base URL, add `AETHEX_BASE_URL` to the `env`.

## Core workflows

> ⚠️ Synthesizing speech, transcribing audio, and placing calls consume Aethex credits.

Everything is driven in natural language. A few examples:

### Text to speech
> "List my available voices, then read this paragraph aloud with the most neutral one."

### Transcription
> "Transcribe this recording and summarize what the caller asked for."

### Voice agents and knowledge
> "Create a voice agent that books dentist appointments, attach our FAQ as a knowledge document, then place a test call to my number."

### Conversations and usage
> "Search my conversations for anyone who mentioned a refund and pull the full transcript of the most recent one."
>
> "Show me this month's usage and which model handled the most minutes."

## Tools

**32 tools across 7 domains.** Every tool runs scoped to the tenant behind your `AETHEX_API_KEY`
and requires that key to carry the listed scope.

### Voices & text-to-speech

| Tool | Scope | Purpose |
|---|---|---|
| `list_voices` | `voices:read` | List the tenant's available voices (global catalog + cloned), with optional `language`/`tag` filters and pagination. |
| `synthesize_speech` | `tts:use` | Synthesize text to speech with a chosen `voice_id`. Returns WAV audio. |
| `preview_voice` | `tts:use` | Render a short preview clip for a voice. Returns WAV audio. |
| `list_tag_vocabulary` | `voices:read` | The controlled vocabulary of voice tags (tone, texture, etc.) for filtering voices. |

### Transcription

| Tool | Scope | Purpose |
|---|---|---|
| `transcribe_audio` | `transcribe:use` | Synchronously transcribe an audio file and return its text. |
| `submit_transcription_job` | `transcribe:use` | Submit an async transcription job (poll for the result; webhooks are REST-only). |
| `get_transcription_job` | `transcribe:use` | Poll an async transcription job's status and result. |
| `cancel_transcription_job` | `transcribe:use` | Cancel a pending async transcription job. |

### Voice agents

| Tool | Scope | Purpose |
|---|---|---|
| `create_agent` | `agents:write` | Create a voice agent (`name`, `system_prompt`, `voice_id` required). |
| `get_agent` | `agents:read` | Fetch a single agent by id. |
| `update_agent` | `agents:write` | Patch an agent; only the fields you pass are changed. |
| `list_agents` | `agents:read` | List the tenant's agents with pagination. |
| `delete_agent` | `agents:write` | Delete an agent. |
| `duplicate_agent` | `agents:write` | Clone an agent along with its knowledge documents. |

### Agent knowledge bases

| Tool | Scope | Purpose |
|---|---|---|
| `upload_knowledge_doc` | `agents:write` | Attach a knowledge document (text or file) to an agent. |
| `list_knowledge_docs` | `agents:read` | List an agent's knowledge documents. |
| `query_knowledge_base` | `agents:read` | Hybrid (vector + keyword) retrieval over an agent's knowledge base. |
| `delete_knowledge_doc` | `agents:write` | Remove a knowledge document from an agent. |

### Calls

| Tool | Scope | Purpose |
|---|---|---|
| `trigger_call` | `calls:write` | Place a single outbound call (returns immediately with `status="queued"`; the dial runs off-request). |
| `get_call` | `calls:read` | Fetch a full call record. |
| `get_call_status` | `calls:read` | Lightweight telephony status for a call. |
| `list_calls` | `calls:read` | List calls with `status`/`direction` filters and pagination. |
| `batch_calls` | `calls:write` | Dispatch a batch of outbound calls (one agent, many recipients). |

### Conversations

| Tool | Scope | Purpose |
|---|---|---|
| `list_conversations` | `conversations:read` | List the tenant's conversations with pagination. |
| `get_conversation` | `conversations:read` | Fetch a single conversation. |
| `get_transcript` | `conversations:read` | Fetch a conversation's turn-by-turn transcript. |
| `search_conversations` | `conversations:read` | Full-text search over conversations. |
| `submit_feedback` | `conversations:read` | Attach a rating and comment to a conversation. |

### Usage & models

| Tool | Scope | Purpose |
|---|---|---|
| `get_usage_summary` | `usage:read` | Usage summary for the tenant (optionally scoped to one API key). |
| `get_daily_usage` | `usage:read` | Daily usage breakdown over a window of days. |
| `get_monthly_usage` | `usage:read` | Monthly usage breakdown. |
| `list_models` | `models:read` | List available models. |

## Configuration

The server is configured entirely through environment variables; only the API key is required.

| Variable | Default | Description |
|---|---|---|
| `AETHEX_API_KEY` | required | Your Aethex API key; the only credential the server needs. |
| `AETHEX_BASE_URL` | `https://api.aethexai.com` | Override the API base URL. Leave unset for production. |
| `AETHEX_MCP_OUTPUT_MODE` | `files` | How audio outputs are returned: `files`, `resources`, or `both`. |
| `AETHEX_MCP_BASE_PATH` | `~/Desktop` | Base directory for saved audio when writing files. |

### Output modes

`AETHEX_MCP_OUTPUT_MODE` controls how the audio-producing tools (`synthesize_speech`, `preview_voice`) return results:

1. **`files`** (default): save the audio to disk and return the file path.
2. **`resources`**: return the audio inline as a base64-encoded MCP resource, with no disk I/O. Handy for containerized or sandboxed clients.
3. **`both`**: save to disk and return the resource; a saved resource can be fetched later via its `aethex://<filename>` URI.

## Troubleshooting

Claude Desktop logs:

- **macOS**: `~/Library/Logs/Claude/mcp-server-Aethex.log`
- **Windows**: `%APPDATA%\Claude\logs\mcp-server-Aethex.log`

**`AETHEX_API_KEY environment variable is required`:** the server refuses to start without a key. Set it in the `env` block of your client config (or your shell), using a valid key from the [developer portal](https://developers.aethexai.com).

**Timeouts on long-running tools:** large transcriptions especially can take a while, and the MCP Inspector may report a timeout even though the tool finished. Prefer `submit_transcription_job` + `get_transcription_job` over a single synchronous call.

**`spawn uvx ENOENT`:** your client can't find `uvx` on its `PATH`. Run `which uvx` and use that absolute path as the `command` (e.g. `/usr/local/bin/uvx`).

## Development

Run from source:

```bash
git clone https://github.com/aethexai/aethexai-mcp
cd aethexai-mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

```bash
./scripts/test.sh                            # pytest (add --verbose / --fail-fast)
uv run fastmcp dev aethexai_mcp/server.py    # explore every tool in the MCP Inspector
```

Questions can be sent to [developers@aethexai.com](mailto:developers@aethexai.com).

## Community

- GitHub: [github.com/aethexai](https://github.com/aethexai)
- X: [@aethexailabs](https://x.com/aethexailabs)
- LinkedIn: [AethexAI](https://www.linkedin.com/company/www.aethexai.com/)
- Discord: [discord.gg/ccyuJNZm7x](https://discord.gg/ccyuJNZm7x)

## License

Released under the [MIT License](LICENSE).
