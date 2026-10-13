"""Test Engineer + Evaluation Specialist contracts (SDD TEST_EVAL_AGENTS)."""
from __future__ import annotations

from pathlib import Path

from sparkforge_azure.agentic.spawn import SpawnContext, decide_spawn
from sparkforge_azure.agentmanifest.model import (
    parse_manifest,
    validate_agents_tree,
)
from sparkforge_azure.agentmanifest.tools import known_tools

REPO = Path(__file__).resolve().parents[1]


def _manifest(agent_id: str):
    return parse_manifest(REPO / "agents" / f"{agent_id}.md")


def test_new_roles_validate_v2() -> None:
    rep = validate_agents_tree(REPO, allow_pending_knowledge=True)
    assert rep.errors == []
    for aid in ("test-engineer", "evaluation-specialist"):
        m = _manifest(aid)
        assert m.family == "test_eval"
        assert m.data["schema_version"] == 2


def test_test_engineer_tool_policy() -> None:
    m = _manifest("test-engineer")
    catalog = known_tools()
    # may inspect tests/code — never mutate the cloud
    for t in m.allowed_tools:
        assert t in catalog
        assert t.startswith("sfa_")
    assert m.data["risk"] in {"read_only", "local_write"}
    assert m.data["risk"] != "cloud_write"
    # read-side tools only — no graph build / lab run mutation verbs
    assert "sfa_lab_run" not in m.allowed_tools
    assert "sfa_graph_build" not in m.allowed_tools


def test_eval_specialist_context_policy() -> None:
    m = _manifest("evaluation-specialist")
    allowed = set(m.allowed_context_kinds)
    # consumes eval-plane artifacts — never raw artifact/tool output
    assert {"eval_result", "metric", "claim"} <= allowed
    assert "artifact" not in allowed
    assert "tool_output" not in allowed
    assert "code" not in allowed
    # required ⊆ allowed (validator already enforces; assert the real manifest)
    assert set(m.required_context_kinds) <= allowed


def test_spawn_by_trigger_not_domain() -> None:
    """test_eval agents spawn via explicit gate triggers — never via domain
    routing, even when a specialist domain is hot."""
    domain_hot = SpawnContext(
        routed_specialists=("adls-specialist",),
        unresolved=("adls:acl denied",),
    )
    for aid in ("test-engineer", "evaluation-specialist"):
        assert decide_spawn(aid, domain_hot, root=REPO).decision != "SPAWN"
    # each trigger class opens the gate
    for trigger in ("change", "review", "release"):
        ctx = SpawnContext(gate_requested=True, unresolved=(f"{trigger}:x",))
        for aid in ("test-engineer", "evaluation-specialist"):
            assert decide_spawn(aid, ctx, root=REPO).decision == "SPAWN", (
                aid, trigger)


def test_eval_agents_have_role_plans() -> None:
    from sparkforge_azure.agentic.role_plans import role_plan_for

    for aid in ("test-engineer", "evaluation-specialist"):
        plan = role_plan_for(aid, REPO)
        assert plan is not None
        assert set(plan.allowed_context) == set(_manifest(aid).allowed_context_kinds)
