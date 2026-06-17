"""Runtime configuration read from the environment at import time.

The only required value is ``AETHEX_API_KEY``. Everything else has a sane
default so a minimal setup is just one env var.
"""

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY: str = os.getenv("AETHEX_API_KEY")
if not API_KEY:
    raise ValueError("AETHEX_API_KEY environment variable is required")

# Optional override of the API origin (e.g. staging). None -> SDK default.
BASE_URL: str | None = os.getenv("AETHEX_BASE_URL")

# How audio/file-producing tools return their output.
OUTPUT_MODE: str = os.getenv("AETHEX_MCP_OUTPUT_MODE", "files").strip().lower()
if OUTPUT_MODE not in {"files", "resources", "both"}:
    raise ValueError("AETHEX_MCP_OUTPUT_MODE must be one of: 'files', 'resources', 'both'")

# Directory where generated files are written. None -> ~/Desktop.
BASE_PATH: str | None = os.getenv("AETHEX_MCP_BASE_PATH")

# Per-request timeout in seconds for the underlying HTTP client.
TIMEOUT: float = float(os.getenv("AETHEX_MCP_TIMEOUT", "60"))
