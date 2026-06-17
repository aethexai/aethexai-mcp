"""Aethex MCP Server.

Exposes Aethex voice-AI platform capabilities — text-to-speech, transcription,
voice agents and their knowledge bases, calls, conversations, and usage — as MCP
tools backed by the public Aethex API. Tools that incur provider cost are marked
with a cost warning in their description; read-only tools are free to use.
"""

import sys

from mcp.server.fastmcp import FastMCP

INSTRUCTIONS = (
    "Aethex voice-AI platform. Tools cover text-to-speech, transcription, "
    "voice agents and their knowledge bases, calls, conversations, and usage. "
    "Every tool runs scoped to the API key's tenant. List voices before "
    "synthesizing, and create an agent before triggering a call."
)

mcp = FastMCP("Aethex", instructions=INSTRUCTIONS)

# Import the tool modules last so that `mcp` already exists when each module's
# `@mcp.tool(...)` decorators run at import time and register their tools.
from aethexai_mcp.tools import (  # noqa: E402,F401
    agents,
    calls,
    conversations,
    knowledge,
    transcription,
    usage,
    voices,
)


def _is_broken_pipe_error(exc: BaseException) -> bool:
    """True if ``exc`` is a BrokenPipeError or a group of only BrokenPipeErrors."""
    if isinstance(exc, BrokenPipeError):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return all(_is_broken_pipe_error(e) for e in exc.exceptions)
    return False


def main():
    """Run the MCP server over stdio, tolerating a closed client pipe."""
    print("Starting Aethex MCP server", file=sys.stderr)
    try:
        mcp.run()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    except (Exception, BaseExceptionGroup) as err:
        if not _is_broken_pipe_error(err):
            raise
    finally:
        try:
            sys.stdout.close()
            sys.stderr.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
