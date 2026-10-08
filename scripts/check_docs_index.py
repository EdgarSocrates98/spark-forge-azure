"""Docs-index gate: every authored doc must be reachable from
``docs/README.md``.

The README is the map of the documentation surface; a doc that ships
unindexed drifts silently out of sight.  Generated artifacts are exempt:
``docs/sdd/**`` (SDD machinery already gates those) and lock files.

Usage: ``python scripts/check_docs_index.py``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "docs" / "README.md"

#: Paths under docs/ that are generated or self-indexed — never required
#: in the README map.
EXEMPT_PREFIXES = ("sdd/", "superpowers/")


def main() -> int:
    text = README.read_text(encoding="utf-8")
    authored = sorted(
        p.relative_to(ROOT / "docs").as_posix()
        for p in (ROOT / "docs").rglob("*.md")
        if not p.relative_to(ROOT / "docs").as_posix().startswith(
            EXEMPT_PREFIXES)
        and p.name != "README.md")
    missing = [d for d in authored if f"docs/{d}" not in text]
    out = {"ok": not missing,
           "authored_docs": len(authored),
           "exempt_prefixes": list(EXEMPT_PREFIXES),
           "missing_index_entries": missing}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
