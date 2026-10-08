"""Generate host mirrors of agents/<id>.md (SDD AGENT_MIRRORS).

Mirrors: ``.claude/agents/custom/sparkforge-azure-<id>.md`` and
``.agents/agents/sparkforge-azure-<id>.md``. The single source is ``agents/``.

Usage::

    python scripts/sync_agent_mirrors.py           # write/refresh mirrors, prune orphans
    python scripts/sync_agent_mirrors.py --check   # exit 1 on drift, write nothing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.agentmanifest.mirrors import (  # noqa: E402
    check_agent_mirrors,
    sync_agent_mirrors,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift and exit 1 if any")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.check:
        drift = check_agent_mirrors(root)
        print(json.dumps({"in_sync": not drift,
                          "drift": [{"path": d.path, "reason": d.reason} for d in drift]},
                         indent=2))
        return 1 if drift else 0
    changed = sync_agent_mirrors(root)
    print(json.dumps({"changed": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
