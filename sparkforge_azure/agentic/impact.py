"""Impact graph — which agents, evals and tests a changed path invalidates.

A change to a manifest invalidates that agent's inventory row and its
declared evals; a change to the routing table invalidates every routing
lab; a change to the taxonomy invalidates the whole fleet. The map below
is data, declared once — not a heuristic that re-derives impact on every
call.

Unknown paths do NOT produce a confident empty answer: they land in
``unresolved`` as ``impact_unknown:<path>`` — the honest signal that the
graph does not cover that surface yet.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Any

from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS

#: All agentic test surfaces a change can invalidate.
AGENTIC_TESTS: tuple[str, ...] = (
    "tests/test_agentic_inventory.py",
    "tests/test_agent_contract_v2.py",
    "tests/test_agent_manifests.py",
    "tests/test_agentic_role_plans.py",
    "tests/test_agentic_spawn.py",
    "tests/test_agentic_test_eval.py",
    "tests/test_agentic_teams.py",
    "tests/test_agentic_spans.py",
    "tests/test_agentic_labs.py",
    "tests/test_agentic_security_lab.py",
)

_FLEET_WIDE = {
    "agents": list(ALL_AGENT_IDS),
    "tests": list(AGENTIC_TESTS),
}

#: Ordered (prefix, impact) rules — first match wins, so most specific
#: prefixes come first. ``<id>`` in tests is expanded with the stem.
_RULES: tuple[tuple[str, dict[str, Any]], ...] = (
    ("agent-teams/", {
        "agents": [],
        "tests": ["tests/test_agentic_teams.py",
                  "tests/test_agentic_inventory.py"],
    }),
    ("agents/", {
        "agents": ["<stem>"],
        "tests": ["tests/test_agent_manifests.py",
                  "tests/test_agent_contract_v2.py",
                  "tests/test_agentic_inventory.py",
                  "tests/test_agentic_role_plans.py",
                  "tests/test_agentic_spawn.py",
                  "tests/test_agentic_teams.py"],
    }),
    ("sparkforge_azure/agentmanifest/model.py", dict(_FLEET_WIDE)),
    ("sparkforge_azure/agentmanifest/routing.py", {
        "agents": [],
        "tests": ["tests/test_agentic_labs.py",
                  "tests/test_agent_manifests.py"],
    }),
    ("sparkforge_azure/agentmanifest/tools.py", {
        "agents": [],
        "tests": ["tests/test_agentic_inventory.py",
                  "tests/test_agent_manifests.py"],
    }),
    ("sparkforge_azure/agentic/spawn.py", {
        "agents": [],
        "tests": ["tests/test_agentic_spawn.py",
                  "tests/test_agentic_teams.py",
                  "tests/test_agentic_labs.py"],
    }),
    ("sparkforge_azure/agentic/role_plans.py", {
        "agents": [],
        "tests": ["tests/test_agentic_role_plans.py",
                  "tests/test_agentic_inventory.py"],
    }),
    ("sparkforge_azure/agentic/teams.py", {
        "agents": [],
        "tests": ["tests/test_agentic_teams.py"],
    }),
    ("sparkforge_azure/agentic/spans.py", {
        "agents": [],
        "tests": ["tests/test_agentic_spans.py"],
    }),
    ("sparkforge_azure/agentic/handoff.py", {
        "agents": [],
        "tests": ["tests/test_agentic_security_lab.py"],
    }),
    ("sparkforge_azure/agentic/trust.py", {
        "agents": [],
        "tests": ["tests/test_agentic_security_lab.py"],
    }),
    ("sparkforge_azure/agentic/security.py", {
        "agents": [],
        "tests": ["tests/test_agentic_security_lab.py"],
    }),
    ("sparkforge_azure/agentic/memory.py", {
        "agents": [],
        "tests": ["tests/test_agentic_security_lab.py"],
    }),
    ("sparkforge_azure/agentic/budget.py", {
        "agents": [],
        "tests": ["tests/test_agentic_labs.py"],
    }),
    ("sparkforge_azure/agentic/inventory.py", {
        "agents": [],
        "tests": ["tests/test_agentic_inventory.py"],
    }),
    ("sparkforge_azure/agentic/fingerprint.py", {
        "agents": [],
        "tests": ["tests/test_agentic_closure.py"],
    }),
    ("sparkforge_azure/agentic/impact.py", {
        "agents": [],
        "tests": ["tests/test_agentic_closure.py"],
    }),
)


def _norm(path: str) -> str:
    """Repo-relative POSIX path — backslashes and ./ prefixes normalized."""
    return PurePosixPath(path.replace("\\", "/").lstrip("./")).as_posix()


def impact_for(paths: Iterable[str]) -> dict[str, Any]:
    """Agents + test surfaces invalidated by ``paths``; unknown -> unresolved."""
    agents: set[str] = set()
    tests: set[str] = set()
    unresolved: list[str] = []
    seen_agents_all = False
    for raw in paths:
        path = _norm(str(raw))
        stem = PurePosixPath(path).stem
        matched = False
        for prefix, impact in _RULES:
            if path == prefix or path.startswith(prefix):
                matched = True
                for a in impact["agents"]:
                    agents.add(stem if a == "<stem>" else a)
                tests.update(impact["tests"])
                if len(impact["agents"]) == len(ALL_AGENT_IDS):
                    seen_agents_all = True
                break
        if not matched:
            unresolved.append(f"impact_unknown:{path}")
    return {
        "agents": sorted(agents),
        "fleet_wide": seen_agents_all,
        "tests": sorted(tests),
        "unresolved": sorted(unresolved),
    }


__all__ = ["AGENTIC_TESTS", "impact_for"]
