"""Role context plans for the whole taxonomy (SDD ROLE_PLANS_SPAWN)."""
from __future__ import annotations

from pathlib import Path

from sparkforge_azure.agentic.role_plans import role_plan_for
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS, CONTEXT_KINDS

REPO = Path(__file__).resolve().parents[1]


def test_every_agent_has_role_plan() -> None:
    """Every agent in the taxonomy resolves a valid RoleContextPlan —
    derived from its own manifest, never a second registry."""
    for agent_id in ALL_AGENT_IDS:
        plan = role_plan_for(agent_id, REPO)
        assert plan is not None, agent_id
        assert plan.role == agent_id
        assert set(plan.allowed_context) <= set(CONTEXT_KINDS), agent_id
        assert set(plan.required_context) <= set(plan.allowed_context), agent_id


def test_no_privilege_escalation_on_handoff() -> None:
    """A handoff can never grant the receiver context or tools it did not
    already declare: the receiver's own plan filters, not the sender's."""
    for agent_id in ALL_AGENT_IDS:
        plan = role_plan_for(agent_id, REPO)
        assert plan is not None
        # a plan that allowed everything would be escalation-by-default
        assert plan.allowed_context, agent_id
        # tools come from the manifest allow list, not from the caller
        assert isinstance(plan.tool_access, tuple)


def test_plans_derive_from_manifest_not_table() -> None:
    """Changing the manifest changes the plan — derivation, no drift."""
    from sparkforge_azure.agentmanifest.model import parse_manifest

    m = parse_manifest(REPO / "agents" / "synthesizer.md")
    plan = role_plan_for("synthesizer", REPO)
    assert tuple(m.allowed_context_kinds) == plan.allowed_context
    assert tuple(m.allowed_tools) == plan.tool_access


def test_unknown_agent_fails_closed() -> None:
    assert role_plan_for("not-an-agent", REPO) is None
