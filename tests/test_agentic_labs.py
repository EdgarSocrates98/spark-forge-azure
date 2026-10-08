"""Agent labs — routing, negative-routing and budget scenarios.

Labs are deterministic scenarios with an oracle: each canonical case must
route to the expected specialist(s) and only them, a case without domain
signal must route nobody, and an exhausted budget must stop the agent with
a named reason — never a silent overflow.
"""
from __future__ import annotations

import pytest

from sparkforge_azure.agentic.budget import (
    AgentBudget,
    BudgetExceededError,
    BudgetStatus,
)
from sparkforge_azure.agentic.spawn import SpawnContext, decide_spawn
from sparkforge_azure.agentmanifest.routing import explain_route, route

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_routing_lab_expected_specialists() -> None:
    """Canonical cases: the expected specialist and only it gets routed."""
    cases = [
        # single-domain utterances -> exactly one specialist
        ("my unity catalog grant was denied on the external location",
         ["unity-catalog-specialist"]),
        ("onelake shortcut pointing at adls returns 403",
         ["onelake-specialist", "adls-specialist"]),
        ("consumer group lag grows on the event hub kafka endpoint",
         ["event-hubs-specialist"]),
        ("purview lineage scan missed a sensitivity label",
         ["purview-specialist"]),
        ("terraform plan fails on azurerm provider",
         ["terraform-specialist"]),
        ("bicep arm template what-if shows wrong sku",
         ["bicep-specialist"]),
        ("spark shuffle spill oom on slow job",
         ["spark-performance-specialist"]),
    ]
    for query, expected in cases:
        routed = route(query)
        for specialist in expected:
            assert specialist in routed, (query, routed)
        assert len(routed) == len(expected), (query, routed, expected)

    # the original motivating case is multi-domain: databricks + uc + adls
    routed = route(
        "azure databricks job cannot access a unity catalog table on adls gen2")
    assert set(routed) == {
        "azure-databricks-specialist",
        "unity-catalog-specialist",
        "adls-specialist",
    }

    # explain_route marks expected as selected and gives matched terms
    report = explain_route("fabric lakehouse shortcut broken")
    decisions = {r["specialist"]: r for r in report}
    assert decisions["onelake-specialist"]["decision"] == "selected"
    assert "shortcut" in decisions["onelake-specialist"]["matched_terms"]
    assert decisions["fabric-specialist"]["decision"] == "selected"


def test_negative_routing_lab() -> None:
    """No domain signal -> nobody routed, nobody spawned."""
    assert route("the weather is nice, let us refactor the stylesheet") == []
    assert route("") == []
    report = explain_route("generic prose with no azure terms")
    assert all(r["decision"] == "no_match" for r in report)
    assert all(r["matched_terms"] == [] for r in report)

    # and the spawn gate agrees: no domain match, no spawn
    ctx = SpawnContext()
    decision = decide_spawn("fabric-specialist", ctx, root=REPO_ROOT)
    assert decision.decision != "SPAWN"


def test_budget_lab_graceful_stop() -> None:
    """Budget exhausted -> named stop, never a silent overflow."""
    budget = AgentBudget(max_tokens=100, max_tool_calls=2,
                         max_time_seconds=60, max_retries=1)
    budget.consume_tokens(80)
    assert budget.status == BudgetStatus.WARNING

    budget.consume_tokens(20)
    assert budget.is_exhausted
    assert budget.status == BudgetStatus.EXHAUSTED

    # crossing the cap raises the named error — the graceful stop signal
    over = AgentBudget(max_tokens=10)
    with pytest.raises(BudgetExceededError, match="tokens"):
        over.consume_tokens(11)

    # every dimension enforces, not just tokens
    calls = AgentBudget(max_tokens=10_000, max_tool_calls=1)
    calls.consume_tool_call()
    with pytest.raises(BudgetExceededError, match="tool_calls"):
        calls.consume_tool_call()

    clock = AgentBudget(max_tokens=10_000, max_tool_calls=99,
                        max_time_seconds=30)
    with pytest.raises(BudgetExceededError, match="time"):
        clock.consume_time(31)
