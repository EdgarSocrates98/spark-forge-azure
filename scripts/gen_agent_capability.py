"""Generate agents/CAPABILITY.json (SDD AGENT_DOD_GATE).

Deterministic snapshot of the fleet: per agent — id, kind, status, domain,
eval refs and host-mirror paths. Source of truth is ``agents/*.md`` via
``inventory()``; this file is an artifact — never edit by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.agentic.inventory import inventory  # noqa: E402
from sparkforge_azure.agentmanifest.mirrors import (  # noqa: E402
    AGENT_MIRROR_ROOTS,
    mirror_name,
)
from sparkforge_azure.agentmanifest.model import (  # noqa: E402
    load_manifests,
    parse_manifest,
)

OUT = ROOT / "agents" / "CAPABILITY.json"


def build(root: Path) -> dict:
    rep = inventory(root)
    load_manifests(root)  # validates the tree the manifests came from
    by_id = {}
    for a in rep.agents:
        src = root / "agents" / f"{a.agent_id}.md"
        by_id[a.agent_id] = (
            parse_manifest(src).data if src.is_file() else {}
        )
    agents = []
    for a in rep.agents:
        data = by_id[a.agent_id]
        agents.append({
            "agent_id": a.agent_id,
            "kind": a.kind,
            "status": a.status,
            "domain": data.get("domain"),
            "evals": data.get("evals") or [],
            "mirrors": [
                f"{mroot}/{mirror_name(a.agent_id)}.md"
                for mroot in AGENT_MIRROR_ROOTS
            ],
        })
    return {"generated_by": "scripts/gen_agent_capability.py",
            "counts": dict(rep.counts), "agents": agents}


def main() -> int:
    payload = json.dumps(build(ROOT), indent=2, ensure_ascii=False) + "\n"
    OUT.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
