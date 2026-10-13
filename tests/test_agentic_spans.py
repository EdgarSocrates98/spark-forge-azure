"""Agent spans, execution receipts and waste (SDD AGENTOPS_AGENT)."""
from __future__ import annotations

from sparkforge_azure.agentic.spans import (
    AgentExecutionReceipt,
    AgentSpan,
    CandidateRecord,
    HandoffRecord,
    agent_value_report,
    agent_waste,
)


def _span(agent: str, **kw) -> AgentSpan:
    base = dict(
        agent_id=agent, family="domain", case_id="case-1", run_id="run-1",
        spawn_reason="routed", spawn_trigger="on_domain_match",
        ended_at=None, stop_reason="work_done",
    )
    base.update(kw)
    return AgentSpan(**base)


def test_agent_span_fields_and_unknown_tokens() -> None:
    s = _span("azure-databricks-specialist", ended_at=10.0)
    s = AgentSpan(**{**s.__dict__, "started_at": 5.0})
    assert s.duration_seconds == 5.0
    # unknown tokens are unresolved, never zero
    assert s.tokens_status == "unresolved"
    assert s.cost_status == "unresolved"
    d = s.to_dict()
    assert d["tokens"] == {"observed": None, "status": "unresolved"}
    assert d["cost"] == {"observed": None, "status": "unresolved"}
    # trace adapter lands on the 'agent' lane
    ts = s.to_trace_span()
    assert ts.component_type == "agent"
    assert ts.name == "agent.azure-databricks-specialist"
    assert ts.metadata["spawn_trigger"] == "on_domain_match"
    # measured tokens report measured
    m = _span("fabric-specialist", tokens_in=100, tokens_out=40)
    assert m.tokens_status == "measured"
    assert m.to_dict()["tokens"]["observed"] == 140


def test_execution_receipt_shape() -> None:
    receipt = AgentExecutionReceipt(
        run_id="run-1", case_id="case-1",
        considered=(
            CandidateRecord("fabric-specialist", "SPAWN", "domain_match", 0.6),
            CandidateRecord("adls-specialist", "SKIP", "below_cap"),
            CandidateRecord("referee", "DEFER", "conditions_unmet"),
        ),
        spans=(_span("fabric-specialist", findings_emitted=2),),
        handoffs=(HandoffRecord("fabric-specialist", "verifier",
                                fields=("finding", "evidence")),),
        budgets={"fabric-specialist": {"tokens": {"used": 140, "cap": 2000}}},
    )
    d = receipt.to_dict()
    assert [c["agent_id"] for c in d["considered"]] == [
        "fabric-specialist", "adls-specialist", "referee"]
    assert d["spawned"] == ["fabric-specialist"]
    assert [c["agent_id"] for c in d["skipped"]] == ["adls-specialist"]
    assert [c["agent_id"] for c in d["deferred"]] == ["referee"]
    assert d["handoffs"][0]["admitted"] is True
    assert d["budgets"]["fabric-specialist"]["tokens"]["cap"] == 2000
    assert d["spans"][0]["findings_emitted"] == 2


def test_waste_detector() -> None:
    # productive span -> no waste
    good = AgentExecutionReceipt(
        run_id="r", case_id="c",
        spans=(_span("fabric-specialist", findings_emitted=1),))
    assert agent_waste(good) == []

    # empty spawn -> observed waste
    empty = AgentExecutionReceipt(
        run_id="r", case_id="c",
        spans=(_span("onelake-specialist"),))
    w = agent_waste(empty)
    assert len(w) == 1
    assert w[0]["pattern"] == "empty_agent_spawn"
    assert w[0]["classification"] == "observed"
    assert "onelake-specialist" in w[0]["description"]

    # a span that only resolved an unresolved item still produced value
    resolved = AgentExecutionReceipt(
        run_id="r", case_id="c",
        spans=(_span("x", unresolved_resolved=1),))
    assert agent_waste(resolved) == []

    # decision change alone is value
    changed = AgentExecutionReceipt(
        run_id="r", case_id="c",
        spans=(_span("y", decisions_changed=1),))
    assert agent_waste(changed) == []

    # same agent twice -> duplicate spawn waste
    dup = AgentExecutionReceipt(
        run_id="r", case_id="c",
        spans=(
            _span("fabric-specialist", findings_emitted=1),
            _span("fabric-specialist", findings_emitted=1),
        ))
    patterns = {f["pattern"] for f in agent_waste(dup)}
    assert patterns == {"duplicate_agent_spawn"}


def test_agentops_report_value_vector() -> None:
    receipt = AgentExecutionReceipt(
        run_id="run-9", case_id="case-9",
        considered=(
            CandidateRecord("fabric-specialist", "SPAWN", "domain_match", 0.6),
            CandidateRecord("adls-specialist", "SKIP", "below_cap"),
        ),
        spans=(
            _span("fabric-specialist", findings_emitted=2, tokens_in=10,
                  tokens_out=5),
            _span("onelake-specialist"),
        ),
        handoffs=(HandoffRecord("fabric-specialist", "verifier",
                                fields=("finding",)),),
    )
    report = agent_value_report(receipt)
    assert report["considered"] == 2
    assert report["spawned"] == 1
    assert report["skipped"] == 1
    agents = report["agents"]
    # per-agent vector: no collapsed score, each axis named
    assert agents["fabric-specialist"]["findings_emitted"] == 2
    assert agents["fabric-specialist"]["tokens"] == {
        "observed": 15, "status": "measured"}
    assert agents["onelake-specialist"]["tokens"] == {
        "observed": None, "status": "unresolved"}
    # no magic score anywhere
    assert "score" not in report
    assert all("score" not in v for v in agents.values())
    # waste surfaced at report level
    assert report["waste"][0]["pattern"] == "empty_agent_spawn"
