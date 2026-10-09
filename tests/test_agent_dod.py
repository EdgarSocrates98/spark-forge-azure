"""Definition of Done per agent family (SDD AGENT_DOD_GATE).

Core (§217): manifest + role plan + tool policy + budget + handoff + routing
+ evals + AgentOps. Specialists add an executable eval suite (§218);
reviewers and subagents are spawn-only — never top-level routes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sparkforge_azure.agentic.inventory import inventory
from sparkforge_azure.agentmanifest.model import (
    ALL_AGENT_IDS,
    ROLE_IDS,
    SPECIALIST_IDS,
    SUBAGENT_IDS,
)
from sparkforge_azure.agentmanifest.routing import ROUTING_TABLE

REPO = Path(__file__).resolve().parents[1]

CORE_DIMS = {
    "manifest", "role_plan", "tool_policy", "budget",
    "handoff", "routing", "evals", "agentops", "autonomy",
}


def test_core_dod_all_agents() -> None:
    rep = inventory(REPO)
    failures = [
        (a.agent_id, d.name)
        for a in rep.agents
        for d in a.dimensions
        if d.name in CORE_DIMS and d.satisfied is not True
    ]
    assert failures == []


def test_role_specific_dod() -> None:
    routed = {rt.specialist for rt in ROUTING_TABLE}
    assert routed == set(SPECIALIST_IDS)
    for sid in SPECIALIST_IDS:
        assert (REPO / "evals" / "agents" / f"{sid}.yaml").is_file(), sid
    spawn_only = (set(ROLE_IDS) - {"coordinator"}) | set(SUBAGENT_IDS)
    for aid in spawn_only:
        assert aid not in routed, f"{aid} must spawn, not route"


def test_capability_manifest_in_sync() -> None:
    cap = REPO / "agents" / "CAPABILITY.json"
    assert cap.is_file()
    regen = subprocess.run(
        [sys.executable, "scripts/gen_agent_capability.py"],
        capture_output=True, text=True, cwd=REPO,
    )
    assert regen.returncode == 0, regen.stderr
    fresh = json.loads(cap.read_text(encoding="utf-8"))
    assert {a["agent_id"] for a in fresh["agents"]} == set(ALL_AGENT_IDS)
    git = subprocess.run(
        ["git", "diff", "--name-only", "--", "agents/CAPABILITY.json"],
        capture_output=True, text=True, cwd=REPO,
    )
    assert git.stdout.strip() == "", "CAPABILITY.json is stale — regenerate it"


def test_new_agent_gate_documented() -> None:
    text = (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8").lower()
    assert "agent" in text and "gate" in text
    for marker in ("all_agent_ids", "evals", "mirror"):
        assert marker in text
