"""Generate a Claude Desktop config block that runs this MCP server.

Run ``python -m aethexai_mcp --print`` to see the JSON, or without ``--print``
to write it into the platform's ``claude_desktop_config.json``.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_claude_config_path() -> Path | None:
    """Return the platform's Claude config directory, or None if not found."""
    if sys.platform == "win32":
        path = Path(Path.home(), "AppData", "Roaming", "Claude")
    elif sys.platform == "darwin":
        path = Path(Path.home(), "Library", "Application Support", "Claude")
    elif sys.platform.startswith("linux"):
        path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"), "Claude")
    else:
        return None

    if path.exists():
        return path
    return None


def generate_config(api_key: str | None = None) -> dict:
    """Build the ``mcpServers`` config that launches the server via ``uvx``."""
    final_api_key = api_key or os.environ.get("AETHEX_API_KEY")
    if not final_api_key:
        print("Error: Aethex API key is required.")
        print("Please either:")
        print("  1. Pass the API key using --api-key argument, or")
        print("  2. Set the AETHEX_API_KEY environment variable, or")
        print("  3. Add AETHEX_API_KEY to your .env file")
        sys.exit(1)

    return {
        "mcpServers": {
            "Aethex": {
                "command": "uvx",
                "args": ["aethexai-mcp"],
                "env": {"AETHEX_API_KEY": final_api_key},
            }
        }
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print config to screen instead of writing to file",
    )
    parser.add_argument(
        "--api-key",
        help="Aethex API key (alternatively, set AETHEX_API_KEY environment variable)",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        help="Custom path to Claude config directory",
    )
    args = parser.parse_args()

    config = generate_config(args.api_key)

    if args.print:
        print(json.dumps(config, indent=2))
    else:
        claude_path = args.config_path if args.config_path else get_claude_config_path()
        if claude_path is None:
            print(
                "Could not find Claude config path automatically. Please specify it using "
                "--config-path argument. The argument should be an absolute path of the "
                "claude_desktop_config.json file."
            )
            sys.exit(1)

        claude_path.mkdir(parents=True, exist_ok=True)
        print("Writing config to", claude_path / "claude_desktop_config.json")
        with open(claude_path / "claude_desktop_config.json", "w") as f:
            json.dump(config, f, indent=2)
