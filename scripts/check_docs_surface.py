"""Docs-surface gate: every locked CLI command and MCP tool must be
documented in the reference docs.

Locks are the source of truth (``docs/surface.lock.json``); the reference
docs are the contract a user reads.  When a verb ships undocumented the
two diverge silently — this script fails when a locked command has no
mention in ``docs/reference/cli.md`` or a locked MCP tool has none in
``docs/reference/mcp-tools.md``.

Usage: ``python scripts/check_docs_surface.py``
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "docs" / "surface.lock.json"
CLI_DOC = ROOT / "docs" / "reference" / "cli.md"
MCP_DOC = ROOT / "docs" / "reference" / "mcp-tools.md"


def _doc_commands(text: str) -> set[str]:
    """Commands mentioned in the CLI reference: tokens in `sparkforge-azure ...`
    code spans and table cells (`cmd sub` and `cmd` alone both count)."""
    found: set[str] = set()
    for m in re.finditer(r"sparkforge-azure ([a-z][a-z0-9-]*(?: [a-z][a-z0-9-]*)?)",
                         text):
        found.add(m.group(1))
        found.add(m.group(1).split()[0])
    # table cells like `run`/`plan` under `lab <op>` sections resolve via the
    # group heading — so also collect `lab <x>` from `## ` headers + cells.
    for m in re.finditer(r"## `sparkforge-azure ([a-z-]+)", text):
        group = m.group(1)
        section = text[m.end():]
        next_h = section.find("\n## ")
        section = section if next_h == -1 else section[:next_h]
        for cell in re.finditer(r"\| `([a-z][a-z0-9-]*)`", section):
            found.add(f"{group} {cell.group(1)}")
            found.add(cell.group(1))
    return found


def main() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    cli_text = CLI_DOC.read_text(encoding="utf-8")
    mcp_text = MCP_DOC.read_text(encoding="utf-8")
    documented = _doc_commands(cli_text)

    missing_cli = [
        c for c in lock["cli"]["commands"]
        if c not in documented and c.split()[0] not in documented
    ]
    tools = lock.get("mcp", {}).get("tools", [])
    names = [t["name"] if isinstance(t, dict) else str(t) for t in tools]
    missing_mcp = [n for n in names if n not in mcp_text]

    out = {
        "ok": not missing_cli and not missing_mcp,
        "cli_commands": len(lock["cli"]["commands"]),
        "mcp_tools": len(names),
        "missing_cli_docs": missing_cli,
        "missing_mcp_docs": missing_mcp,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
