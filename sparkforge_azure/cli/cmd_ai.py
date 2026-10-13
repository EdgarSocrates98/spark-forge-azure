"""``sparkforge-azure ai [host]`` — observe AI hosts; ``--launch`` opens one (TTY only)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sparkforge_azure.distribution.ai import HOST_NAMES, ai_flow


def _ai(args: argparse.Namespace) -> dict[str, Any]:
    return ai_flow(
        args.host or "all",
        repo=Path.cwd(),
        launch=args.launch,
    )


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "ai",
        help="observe AI host state (binary/version/auth/integration); "
             "--launch opens it (CLI+TTY only, never via MCP)",
    )
    p.add_argument(
        "host",
        nargs="?",
        choices=(*HOST_NAMES, "all"),
        default="all",
        help="host to observe (default: all)",
    )
    p.add_argument(
        "--launch",
        action="store_true",
        help="launch the host CLI in this repo — requires a single host and a TTY",
    )
    p.set_defaults(func=_ai)
