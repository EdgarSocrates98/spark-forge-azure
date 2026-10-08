"""``sparkforge-azure`` -- the official CLI (section 0).

Principles (section 182): scriptable, JSON-friendly, deterministic,
non-interactive.  Every command prints exactly one JSON document on stdout
(``--format text`` is a human convenience, never the contract) and returns an
exit code: 0 ok, 1 findings/blocked result, 2 usage or refused input.

Command families register themselves from a CLOSED list of modules
(``COMMAND_MODULES``).  Each module exposes ``register(sub)`` where ``sub`` is
the argparse sub-parser collection; each leaf sets ``func=callable(args)->dict``.
The list being closed is what makes the CLI surface lockable (section 87).
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any

from sparkforge_azure import __version__
from sparkforge_azure.cli import CliError

PROG = "sparkforge-azure"

COMMAND_MODULES: tuple[str, ...] = (
    "sparkforge_azure.cli.cmd_core",
    "sparkforge_azure.cli.cmd_tokensave",
    "sparkforge_azure.cli.cmd_governance",
    "sparkforge_azure.cli.cmd_doctor",
    "sparkforge_azure.cli.cmd_graph",
    "sparkforge_azure.cli.cmd_collect",
    "sparkforge_azure.cli.cmd_bundle",
    "sparkforge_azure.cli.cmd_lab",
    "sparkforge_azure.cli.cmd_mcp",
    "sparkforge_azure.cli.cmd_diagnose",
    "sparkforge_azure.cli.cmd_migration",
    "sparkforge_azure.cli.cmd_sdd",
    "sparkforge_azure.cli.cmd_agentops",
)

Result = dict[str, Any]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Spark Forge Azure - Agentic Engineering OS for Azure Data Engineering.",
    )
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}")
    parser.add_argument(
        "--format", choices=("json", "text"), default="json", help="output format (default json)"
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    for name in COMMAND_MODULES:
        importlib.import_module(name).register(sub)
    return parser


def command_paths(parser: argparse.ArgumentParser | None = None) -> list[str]:
    """Every leaf command path, sorted. Used by the surface lock."""
    parser = parser or build_parser()
    out: list[str] = []

    def walk(p: argparse.ArgumentParser, prefix: list[str]) -> None:
        subs = [a for a in p._actions if isinstance(a, argparse._SubParsersAction)]
        if not subs:
            out.append(" ".join(prefix))
            return
        for action in subs:
            for name, child in action.choices.items():
                walk(child, [*prefix, name])

    walk(parser, [])
    return sorted(x for x in out if x)


def _emit(result: Result, fmt: str) -> None:
    if fmt == "text":
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            sys.stdout.write(f"{key}: {value}\n")
        return
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func: Callable[[argparse.Namespace], Result] | None = getattr(args, "func", None)
    if func is None:
        parser.print_help(sys.stderr)
        return 2
    try:
        result = func(args)
    except CliError as exc:
        _emit({"status": "refused", "error": str(exc)}, "json")
        return 2
    _emit(result, args.format)
    status = result.get("status", "ok")
    return 0 if status in {"ok", "pass", "sufficient"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
