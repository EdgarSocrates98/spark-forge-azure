"""SDD MIGRATION_PLANNER — topological waves, cycle -> REVIEW, rollback
on every wave, shared-upstream blocker surfacing."""
from __future__ import annotations

from sparkforge_azure.findings.models import Fact
from sparkforge_azure.migration import planner


def _asset(aid: str) -> Fact:
    return Fact(kind="mig.pipeline",
                subject={"pipeline_id": aid},
                attrs={"name": aid}, provenance={"source": "t"})


def _dep(src: str, dst: str, relation: str = "depends_on") -> Fact:
    return Fact(kind="dep.edge",
                subject={"src": src, "relation": relation, "dst": dst},
                attrs={}, provenance={"source": "t"})


def test_waves_topological_order():
    """AC1: A depends_on B -> B lands in an earlier or equal wave."""
    facts = [_asset("a"), _asset("b"), _dep("a", "b")]
    plan = planner.plan_waves(facts, {"a": "READY", "b": "READY"})
    assert plan["status"] == "ok"
    wave_of = {a: w["wave"] for w in plan["waves"] for a in w["assets"]}
    assert wave_of["b"] < wave_of["a"]
    assert plan["wave_count"] == 2


def test_cycle_is_review_not_fake_order():
    """AC2: dependency cycle -> REVIEW + cycle members, never invented
    ordering."""
    facts = [_asset("a"), _asset("b"),
             _dep("a", "b"), _dep("b", "a")]
    plan = planner.plan_waves(facts, {"a": "READY", "b": "READY"})
    assert plan["status"] == "REVIEW"
    assert set(plan["cycle"]) == {"a", "b"}
    assert plan["waves"] == []


def test_wave_has_rollback():
    """AC3: every wave carries trigger + steps + divergence policy."""
    facts = [_asset("a"), _asset("b"), _dep("a", "b")]
    plan = planner.plan_waves(facts, {"a": "READY", "b": "READY"})
    for w in plan["waves"]:
        rb = w["rollback"]
        assert rb["trigger"] and rb["steps"]
        assert rb["data_divergence_policy"]
        assert w["receipt"]["asset_count"] == len(w["assets"])


def test_shared_upstream_blocks_wave():
    """AC4: a ready asset whose upstream is blocked/unresolved surfaces
    as a blocker — never silently scheduled."""
    facts = [_asset("a"), _asset("b"), _dep("a", "b")]
    blockers = planner.shared_upstream_blockers(
        facts, {"a": "READY", "b": "BLOCKED"})
    assert blockers == [{"asset": "a", "blocked_by": "b",
                         "upstream_state": "BLOCKED"}]
    plan = planner.plan_waves(facts, {"a": "READY", "b": "BLOCKED"})
    # b is never placed; a can still schedule (its dep is pending)
    assert plan["pending"]["b"] == "BLOCKED"
    placed = {x for w in plan["waves"] for x in w["assets"]}
    assert "b" not in placed


def test_multi_dependency_edges_all_respected():
    """An asset with two depends_on edges waits for both."""
    facts = [_asset("a"), _asset("b"), _asset("c"),
             _dep("a", "b"), _dep("a", "c")]
    plan = planner.plan_waves(
        facts, {"a": "READY", "b": "READY", "c": "READY"})
    wave_of = {x: w["wave"] for w in plan["waves"] for x in w["assets"]}
    assert wave_of["b"] < wave_of["a"]
    assert wave_of["c"] < wave_of["a"]
