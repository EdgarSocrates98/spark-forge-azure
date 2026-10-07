"""Validate skills, agent manifests and skill mirrors; print a JSON summary.

Exit code 1 on any violation. ``--allow-pending-knowledge`` accepts ``knowledge_refs`` whose
directory does not exist yet (they are reported under ``pending_knowledge``); the default strict
mode requires every referenced knowledge directory to exist.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.agentmanifest.model import (  # noqa: E402
    ROLE_IDS,
    SPECIALIST_IDS,
    SUBAGENT_IDS,
    validate_agents_tree,
)
from sparkforge_azure.skills.mirrors import check_mirrors  # noqa: E402
from sparkforge_azure.skills.model import discover_skill_files, validate_skills_tree  # noqa: E402


def run(root: Path, *, allow_pending_knowledge: bool = False) -> dict:
    skills = validate_skills_tree(root, allow_pending_knowledge=allow_pending_knowledge)
    agents = validate_agents_tree(root, allow_pending_knowledge=allow_pending_knowledge)
    drift = check_mirrors(root)
    errors = skills.errors + agents.errors + [f"mirror {d.reason}: {d.path}" for d in drift]
    return {
        "ok": not errors,
        "mode": "allow-pending-knowledge" if allow_pending_knowledge else "strict",
        "skills": len(discover_skill_files(root)),
        "agents": {"roles": len(ROLE_IDS), "specialists": len(SPECIALIST_IDS),
                   "subagents": len(SUBAGENT_IDS)},
        "mirrors_in_sync": not drift,
        "pending_knowledge": sorted(set(skills.pending_knowledge + agents.pending_knowledge)),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skills, agents and mirrors.")
    parser.add_argument("--allow-pending-knowledge", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    summary = run(args.root.resolve(), allow_pending_knowledge=args.allow_pending_knowledge)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
