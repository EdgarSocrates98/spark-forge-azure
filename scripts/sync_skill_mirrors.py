"""Generate host mirrors of skills/<name>/SKILL.md (section 159).

Mirrors: ``.claude/skills/sparkforge-azure-<name>/SKILL.md`` and
``.agents/skills/sparkforge-azure-<name>/SKILL.md``. The single source is ``skills/``.

Usage::

    python scripts/sync_skill_mirrors.py           # write/refresh mirrors, prune orphans
    python scripts/sync_skill_mirrors.py --check   # exit 1 on drift, write nothing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.skills.mirrors import check_mirrors, sync_mirrors  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift and exit 1 if any")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.check:
        drift = check_mirrors(root)
        print(json.dumps({"in_sync": not drift,
                          "drift": [{"path": d.path, "reason": d.reason} for d in drift]},
                         indent=2))
        return 1 if drift else 0
    changed = sync_mirrors(root)
    print(json.dumps({"changed": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
