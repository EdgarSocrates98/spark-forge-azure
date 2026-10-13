"""Spawn gate — SPAWN | SKIP | DEFER (SDD ROLE_PLANS_SPAWN)."""
from __future__ import annotations

import json
from pathlib import Path

from sparkforge_azure.agentic.spawn import (
    SPAWN_DECISIONS,
    SpawnContext,
    decide_spawn,
    decide_team,
)
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS, SPECIALIST_IDS
from sparkforge_azure.agentmanifest.routing import explain_route
from sparkforge_azure.cli.main import main

REPO = Path(__file__).resolve().parents[1]


def test_spawn_decision_closed_vocabulary() -> None:
    ctx = SpawnContext(
        routed_specialists=("unity-catalog-specialist",),
        unresolved=("unity-catalog:grant missing",),
    )
    for agent_id in ALL_AGENT_IDS:
        d = decide_spawn(agent_id, ctx, root=REPO)
        assert d.decision in SPAWN_DECISIONS, (agent_id, d.decision)
        assert d.reason
        assert d.to_dict()["decision"] == d.decision


def test_spawn_gate_semantics() -> None:
    # no domain match and nothing in scope -> SKIP/DEFER, never SPAWN
    empty = SpawnContext()
    d = decide_spawn("adls-specialist", empty, root=REPO)
    assert d.decision in {"SKIP", "DEFER"}
    # routed domain with unresolved uncertainty -> SPAWN
    hot = SpawnContext(
        routed_specialists=("adls-specialist",),
        unresolved=("adls:acl denied on abfss path",),
    )
    d = decide_spawn("adls-specialist", hot, root=REPO)
    assert d.decision == "SPAWN"
    assert d.reason == "routed_with_unresolved_in_scope"
    # routed but no unresolved yet -> DEFER (inputs pending)
    pending = SpawnContext(routed_specialists=("adls-specialist",))
    d = decide_spawn("adls-specialist", pending, root=REPO)
    assert d.decision == "DEFER"
    # not routed -> never SPAWN
    d = decide_spawn("iceberg-specialist", hot, root=REPO)
    assert d.decision != "SPAWN"
    # completed agents never respawn
    done = SpawnContext(
        routed_specialists=("adls-specialist",),
        unresolved=("adls:x",),
        completed_agents=("adls-specialist",),
    )
    assert decide_spawn("adls-specialist", done, root=REPO).decision == "SKIP"


def test_information_gain_threshold_gates() -> None:
    # a routed specialist whose domain has zero matching unresolved is below
    # its declared threshold -> SKIP with the named reason
    ctx = SpawnContext(
        routed_specialists=("adls-specialist",),
        unresolved=("fabric:capacity throttled",),  # wrong domain
    )
    d = decide_spawn("adls-specialist", ctx, root=REPO)
    assert d.decision == "SKIP"
    assert d.reason == "below_information_gain_threshold"


def test_route_explainability() -> None:
    q = "PERMISSION_DENIED no Unity Catalog lendo ADLS via abfss atrás de private endpoint"
    explained = explain_route(q)
    assert {r["specialist"] for r in explained} == set(SPECIALIST_IDS)
    by_decision = {r["specialist"]: r for r in explained}
    assert by_decision["unity-catalog-specialist"]["decision"] == "selected"
    assert by_decision["adls-specialist"]["decision"] == "selected"
    assert by_decision["networking-specialist"]["decision"] == "selected"
    assert by_decision["unity-catalog-specialist"]["matched_terms"]
    assert by_decision["bicep-specialist"]["decision"] == "no_match"
    # deterministic: same query, identical explanation
    assert explain_route(q) == explained


def test_spawn_for_reviewers_is_conditional() -> None:
    # reviewer spawns only when findings exist (never on the hot path)
    no_findings = SpawnContext(routed_specialists=("adls-specialist",))
    d = decide_spawn("reviewer", no_findings, root=REPO)
    assert d.decision == "DEFER"
    with_findings = SpawnContext(findings=("f1",))
    assert decide_spawn("reviewer", with_findings, root=REPO).decision == "SPAWN"
    # referee only on genuine conflict
    assert decide_spawn("referee", with_findings, root=REPO).decision == "DEFER"
    hot = SpawnContext(conflicts=("uc-vs-adls:verdict disagreement",))
    assert decide_spawn("referee", hot, root=REPO).decision == "SPAWN"


def test_subagent_spawns_via_parent() -> None:
    # parent spawned + delegated scope unresolved -> SPAWN
    ctx = SpawnContext(
        spawned_parents=("azure-databricks-specialist",),
        unresolved=("databricks:uc grant drift",),
    )
    d = decide_spawn("databricks-uc-reviewer", ctx, root=REPO)
    assert d.decision == "SPAWN"
    # parent spawned but nothing unresolved in scope -> below threshold
    nothing = SpawnContext(spawned_parents=("azure-databricks-specialist",))
    assert decide_spawn(
        "databricks-uc-reviewer", nothing, root=REPO).decision == "SKIP"
    # no parent spawn -> DEFER (inputs cannot exist)
    no_parent = SpawnContext(unresolved=("databricks:uc grant drift",))
    assert decide_spawn(
        "databricks-uc-reviewer", no_parent, root=REPO).decision == "DEFER"


def test_test_eval_agents_off_hot_path() -> None:
    """test-engineer / evaluation-specialist spawn only via the eval gate."""
    ctx = SpawnContext(
        routed_specialists=("adls-specialist",), unresolved=("adls:x",))
    assert decide_spawn("test-engineer", ctx, root=REPO).decision != "SPAWN"
    gated = SpawnContext(gate_requested=True, unresolved=("x",))
    assert decide_spawn("test-engineer", gated, root=REPO).decision == "SPAWN"
    assert decide_spawn("evaluation-specialist", gated, root=REPO).decision == "SPAWN"


def test_decide_team_deterministic() -> None:
    ctx = SpawnContext(
        routed_specialists=("adls-specialist",), unresolved=("adls:x",))
    a = decide_team(["adls-specialist", "reviewer"], ctx, root=REPO)
    b = decide_team(["adls-specialist", "reviewer"], ctx, root=REPO)
    assert [d.to_dict() for d in a] == [d.to_dict() for d in b]


def test_cli_route_explain(capsys) -> None:
    assert main(["agents", "route",
                 "PERMISSION_DENIED Unity Catalog ADLS private endpoint"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert "unity-catalog-specialist" in out["selected"]
    assert len(out["candidates"]) == len(SPECIALIST_IDS)
    assert out["spawn"]["unity-catalog-specialist"]["decision"] == "SPAWN"
