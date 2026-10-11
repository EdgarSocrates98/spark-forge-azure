"""``sparkforge-azure portal`` — optional local web UI over the real services.

Why: one local screen with the install dashboard, AI hosts, MCP
handshake, skills/agents catalog, safe tasks and graph — the same
engine and receipts as the CLI, no flags to learn. When to use: first
onboarding, host configuration, state audit. The portal is a human
boundary — it never runs inside MCP, and CLI/TUI/MCP keep working
without it.
"""

from __future__ import annotations

import argparse
from typing import Any


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure import portal_adapter

    return portal_adapter._portal(args)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "portal",
        help="open the optional local web portal (127.0.0.1, session token) "
             "over the same services as the CLI — never inside MCP",
    )
    p.add_argument(
        "--no-browser",
        action="store_true",
        help="only print the session URL — SSH/headless or manual open",
    )
    p.add_argument(
        "--port",
        type=int,
        default=0,
        help="fixed port (default: a free port of the system)",
    )
    p.add_argument(
        "--root",
        default=None,
        help="workspace to inspect (default: cwd)",
    )
    p.set_defaults(func=_run)
