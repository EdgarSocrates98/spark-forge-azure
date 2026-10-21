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
    "sparkforge_azure.cli.cmd_ai",
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
    "sparkforge_azure.cli.cmd_agents",
    "sparkforge_azure.cli.cmd_agentops",
    "sparkforge_azure.cli.cmd_analyze",
    "sparkforge_azure.cli.cmd_distribution",
    "sparkforge_azure.cli.cmd_install",
    "sparkforge_azure.cli.cmd_portal",
    "sparkforge_azure.cli.cmd_workspace",
    "sparkforge_azure.cli.cmd_context",
    "sparkforge_azure.cli.cmd_delegation",
)

Result = dict[str, Any]


_TOP_COMMANDS: tuple[tuple[str, str], ...] = (
    ("doctor", "health-check the workspace and runtime"),
    ("analyze", "extract facts from an artifact"),
    ("distribution", "install/distribution lifecycle (status, doctor, detach)"),
    ("workspace", "workspace status and management"),
    ("lab", "experiments and lab runs"),
    ("sdd", "spec-driven development pipeline"),
)


class _AzureParser(argparse.ArgumentParser):
    """DX contract: unknown verbs suggest, never just list."""

    def error(self, message: str) -> None:  # noqa: D102
        import difflib
        import re

        m = re.search(r"invalid choice: '([^']+)'", message)
        choices: list[str] = []
        for a in self._actions:
            if isinstance(a, argparse._SubParsersAction):
                choices += list(a.choices)
        if m and choices:
            close = difflib.get_close_matches(m.group(1), choices, n=3, cutoff=0.6)
            if close:
                message += "\n\ndid you mean: " + ", ".join(close) + "?"
        super().error(message)


def _bare_summary(parser: argparse.ArgumentParser) -> int:
    """Bare ``sparkforge-azure``: product summary + path to help.
    Never an error, never a mutation."""
    print("sparkforge-azure - Agentic Engineering OS for Azure Data Engineering.")
    print()
    print("most used:")
    for name, desc in _TOP_COMMANDS:
        print(f"  {name:<14} {desc}")
    print()
    print("help:    sparkforge-azure help <command>  |  sparkforge-azure --help")
    print("docs:    docs/installation/quickstart.md")
    return 0


def _help_for(parser: argparse.ArgumentParser, argv: list[str]) -> int:
    target = argv[1] if len(argv) > 1 else None
    if not target:
        parser.print_help()
        return 0
    for a in parser._actions:
        if isinstance(a, argparse._SubParsersAction) and target in a.choices:
            a.choices[target].print_help()
            return 0
    print(f"sparkforge-azure help: unknown command {target!r}", file=sys.stderr)
    print("see: sparkforge-azure --help", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = _AzureParser(
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
    # forge/* install docs render through the shared kit when the caller
    # asked for text — explicitly (--format text) or via the TUI seam
    # (FORGE_TEXT_OUTPUT in a captured subprocess). Other results keep
    # the flat key: value dump; JSON stays the contract default.
    import os

    forge_doc = isinstance(result, dict) and (
        str(result.get("schema", "")).startswith("forge/")
        or "checks" in result
        or "drift" in result
    )
    if (fmt == "text" or os.environ.get("FORGE_TEXT_OUTPUT")) and forge_doc:
        try:
            from sparkforge_azure.ui.kit import UIContext, format_status_doc

            sys.stdout.write(format_status_doc(result, ctx=UIContext.detect()) + "\n")
            return
        except ImportError:
            pass
    if fmt == "text":
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            sys.stdout.write(f"{key}: {value}\n")
        return
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    _stdio_utf8()
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        try:
            import sys as _sys

            if _sys.stdin.isatty() and _sys.stdout.isatty():
                from sparkforge_azure.ui.home import run_home
                from sparkforge_azure.ui.kit import NonInteractive

                try:
                    return run_home()
                except NonInteractive:
                    pass
        except ImportError:
            pass
        return _bare_summary(parser)
    if argv[0] == "help":
        return _help_for(parser, argv)
    if argv == ["install"] and sys.stdin.isatty() and sys.stdout.isatty():
        from sparkforge_azure.cli.cmd_install import run_guided_install

        return run_guided_install()
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
    # forge/* receipts add: completed/planned/healthy/unverified (success
    # family) — every other non-ok status stays a failure exit. Kit checks
    # report uppercase PASS/FAIL — normalize before comparing.
    return (
        0
        if str(status).lower()
        in {"ok", "pass", "sufficient", "completed", "planned", "healthy", "unverified"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
