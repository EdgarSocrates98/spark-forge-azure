"""Agent-level observability — AgentSpan, AgentExecutionReceipt, value report.

The persisted trace (``observability/tracer``) already carries
``component_type="agent"`` lanes in the timeline; this module is the semantic
layer the runtime produces *before* persistence. An ``AgentSpan`` is what one
spawned agent measurably did — not "the model thought", but fields with a
measurement status:

* ``tokens``/``cost`` are ``None`` when no provider/price source exists —
  ``tokens_status``/``cost_status`` name the hole instead of hiding a zero
  (Observed ≠ Estimated · Unknown ≠ Zero);
* outputs are counts the agent's own result declared — ``facts_emitted``,
  ``findings_emitted``, ``unresolved_resolved``, ``decisions_changed`` — never
  inferred from prose;
* ``stop_reason`` comes from the closed stop vocabulary.

``AgentExecutionReceipt`` is the case-level receipt: every agent the gate
considered (with its SPAWN/SKIP/DEFER reason), every span produced, every
handoff, and per-agent budget consumption. It is the durable evidence that
the fleet earned — or wasted — its budget.

``agent_waste`` flags a spawned agent that produced nothing and changed
nothing: zero facts, zero findings, zero unresolved resolved, zero decisions
changed. That is ``observed`` waste — the run paid for a spawn whose only
output was context.

``agent_value_report`` aggregates a value *vector* per agent. There is no
single score on purpose: value is multi-axis, and collapsing it into one
number would hide exactly the axis that failed.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sparkforge_azure.observability.tracer import TraceSpan

#: Closed outcome vocabulary for an agent run.
SPAN_OUTCOMES: tuple[str, ...] = ("ok", "blocked", "refused", "error")
#: Closed waste patterns attributable to agent-level spans.
AGENT_WASTE_PATTERNS: tuple[str, ...] = (
    "empty_agent_spawn",      # spawned, produced nothing, changed nothing
    "duplicate_agent_spawn",  # same agent spawned twice in one case
)


@dataclass(frozen=True)
class AgentSpan:
    """One agent's measured execution inside a case."""

    agent_id: str
    family: str
    case_id: str
    run_id: str
    spawn_reason: str
    spawn_trigger: str
    context_consumed: tuple[str, ...] = ()
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    stop_reason: str = ""
    outcome: str = "ok"
    facts_emitted: int = 0
    findings_emitted: int = 0
    unresolved_resolved: int = 0
    decisions_changed: int = 0
    handoffs_sent: int = 0
    handoffs_received: int = 0
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    cost_basis: str = ""
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    # §122 — runtime execution fields (empty = not a runtime span)
    runtime: str = ""
    execution_mode: str = ""
    runtime_spawn_id: str = ""
    output_valid: bool | None = None
    tool_calls: int = 0

    @property
    def tokens_status(self) -> str:
        if self.tokens_in is None and self.tokens_out is None:
            return "unresolved"
        return "measured"

    @property
    def cost_status(self) -> str:
        if self.cost_usd is None or not self.cost_basis:
            return "unresolved"
        return "measured"

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return max(0.0, self.ended_at - self.started_at)

    def produced_value(self) -> bool:
        """Any artifact or decision change attributable to this span."""
        return any((
            self.facts_emitted,
            self.findings_emitted,
            self.unresolved_resolved,
            self.decisions_changed,
        ))

    def to_trace_span(self) -> TraceSpan:
        """Adapter into the persisted trace — the 'agent' lane already exists."""
        return TraceSpan(
            span_id=self.span_id,
            run_id=self.run_id,
            parent_span_id=None,
            name=f"agent.{self.agent_id}",
            component_type="agent",
            start_time=self.started_at,
            end_time=self.ended_at,
            input_tokens=self.tokens_in or 0,
            output_tokens=self.tokens_out or 0,
            estimated_cost_usd=self.cost_usd or 0.0,
            status="ok" if self.outcome == "ok" else "error",
            outcome=self.outcome,
            cost_basis=self.cost_basis,
            tokens_status="unresolved" if self.tokens_status == "unresolved" else "",
            metadata={
                "agent_id": self.agent_id,
                "family": self.family,
                "case_id": self.case_id,
                "spawn_reason": self.spawn_reason,
                "spawn_trigger": self.spawn_trigger,
                "context_consumed": list(self.context_consumed),
                "stop_reason": self.stop_reason,
                "facts_emitted": self.facts_emitted,
                "findings_emitted": self.findings_emitted,
                "unresolved_resolved": self.unresolved_resolved,
                "decisions_changed": self.decisions_changed,
                "handoffs_sent": self.handoffs_sent,
                "handoffs_received": self.handoffs_received,
                "runtime": self.runtime,
                "execution_mode": self.execution_mode,
                "runtime_spawn_id": self.runtime_spawn_id,
                "output_valid": self.output_valid,
                "tool_calls": self.tool_calls,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "agent_id": self.agent_id,
            "family": self.family,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "spawn_reason": self.spawn_reason,
            "spawn_trigger": self.spawn_trigger,
            "context_consumed": list(self.context_consumed),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "stop_reason": self.stop_reason,
            "outcome": self.outcome,
            "facts_emitted": self.facts_emitted,
            "findings_emitted": self.findings_emitted,
            "unresolved_resolved": self.unresolved_resolved,
            "decisions_changed": self.decisions_changed,
            "handoffs_sent": self.handoffs_sent,
            "handoffs_received": self.handoffs_received,
            "tokens": {"observed": (
                None if self.tokens_status == "unresolved"
                else (self.tokens_in or 0) + (self.tokens_out or 0)),
                "status": self.tokens_status},
            "cost": {"observed": self.cost_usd, "status": self.cost_status},
            "runtime": self.runtime,
            "execution_mode": self.execution_mode,
            "runtime_spawn_id": self.runtime_spawn_id,
            "output_valid": self.output_valid,
            "tool_calls": self.tool_calls,
        }


@dataclass(frozen=True)
class CandidateRecord:
    """One gate decision as recorded on the receipt."""

    agent_id: str
    decision: str
    reason: str
    expected_gain: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "decision": self.decision,
            "reason": self.reason,
            "expected_gain": self.expected_gain,
        }


@dataclass(frozen=True)
class HandoffRecord:
    """One DATA_ONLY handoff as recorded on the receipt."""

    source: str
    target: str
    fields: tuple[str, ...] = ()
    admitted: bool = True
    refusal: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "fields": list(self.fields),
            "admitted": self.admitted,
            "refusal": self.refusal,
        }


@dataclass(frozen=True)
class AgentExecutionReceipt:
    """Case-level receipt — who was considered, who ran, what they produced."""

    run_id: str
    case_id: str
    considered: tuple[CandidateRecord, ...] = ()
    spans: tuple[AgentSpan, ...] = ()
    handoffs: tuple[HandoffRecord, ...] = ()
    #: ``agent_id -> usage dict`` — tokens/cost/context as consumed vs. the
    #: manifest budget. ``None``-valued axes stay absent, never zero.
    budgets: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def spawned(self) -> tuple[CandidateRecord, ...]:
        return tuple(c for c in self.considered if c.decision == "SPAWN")

    @property
    def skipped(self) -> tuple[CandidateRecord, ...]:
        return tuple(c for c in self.considered if c.decision == "SKIP")

    @property
    def deferred(self) -> tuple[CandidateRecord, ...]:
        return tuple(c for c in self.considered if c.decision == "DEFER")

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "case_id": self.case_id,
            "considered": [c.to_dict() for c in self.considered],
            "spawned": [c.agent_id for c in self.spawned],
            "skipped": [c.to_dict() for c in self.skipped],
            "deferred": [c.to_dict() for c in self.deferred],
            "spans": [s.to_dict() for s in self.spans],
            "handoffs": [h.to_dict() for h in self.handoffs],
            "budgets": {k: dict(v) for k, v in self.budgets.items()},
        }


def agent_waste(receipt: AgentExecutionReceipt) -> list[dict[str, Any]]:
    """Observed agent-level waste on a receipt.

    ``empty_agent_spawn``: the agent ran and produced no facts, no findings,
    resolved no unresolved item and changed no decision. ``hypothesis``
    never applies — an empty output is measured, not guessed.
    """
    findings: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for span in receipt.spans:
        seen[span.agent_id] = seen.get(span.agent_id, 0) + 1
        if not span.produced_value():
            findings.append({
                "pattern": "empty_agent_spawn",
                "classification": "observed",
                "evidence": [span.span_id],
                "description": (
                    f"{span.agent_id} spawned ({span.spawn_trigger}) and emitted "
                    "no facts, findings, resolved-unresolved or decisions"),
            })
    for agent_id, count in seen.items():
        if count > 1:
            ids = [s.span_id for s in receipt.spans if s.agent_id == agent_id]
            findings.append({
                "pattern": "duplicate_agent_spawn",
                "classification": "observed",
                "evidence": list(ids),
                "description": f"{agent_id} spawned {count} times in one case",
            })
    return findings


def _merge_status(statuses: list[str]) -> str:
    if not statuses:
        return "not_applicable"
    if any(s == "measured" for s in statuses):
        return "measured" if all(s == "measured" for s in statuses) else "partial"
    return "unresolved"


def agent_value_report(receipt: AgentExecutionReceipt) -> dict[str, Any]:
    """Per-agent value vector — multi-axis, no collapsed score.

    Each agent reports what it emitted and what it consumed, each axis with
    its own measurement status. Agents considered-but-skipped appear too —
    their value was *not paying* for a useless spawn.
    """
    per_agent: dict[str, dict[str, Any]] = {}
    for span in receipt.spans:
        entry = per_agent.setdefault(span.agent_id, {
            "family": span.family,
            "spans": 0,
            "facts_emitted": 0,
            "findings_emitted": 0,
            "unresolved_resolved": 0,
            "decisions_changed": 0,
            "handoffs_sent": 0,
            "handoffs_received": 0,
            "stop_reasons": [],
            "tokens": {"observed": 0, "status": "not_applicable"},
            "cost": {"observed": 0.0, "status": "not_applicable"},
            "_tokens_statuses": [],
            "_cost_statuses": [],
        })
        entry["spans"] += 1
        entry["facts_emitted"] += span.facts_emitted
        entry["findings_emitted"] += span.findings_emitted
        entry["unresolved_resolved"] += span.unresolved_resolved
        entry["decisions_changed"] += span.decisions_changed
        entry["handoffs_sent"] += span.handoffs_sent
        entry["handoffs_received"] += span.handoffs_received
        if span.stop_reason:
            entry["stop_reasons"].append(span.stop_reason)
        if span.tokens_status == "measured":
            entry["tokens"]["observed"] += (
                (span.tokens_in or 0) + (span.tokens_out or 0))
        if span.cost_status == "measured":
            entry["cost"]["observed"] += span.cost_usd or 0.0
        entry["_tokens_statuses"].append(span.tokens_status)
        entry["_cost_statuses"].append(span.cost_status)

    for entry in per_agent.values():
        entry["tokens"]["status"] = _merge_status(entry.pop("_tokens_statuses"))
        entry["cost"]["status"] = _merge_status(entry.pop("_cost_statuses"))
        if entry["tokens"]["status"] != "measured":
            entry["tokens"]["observed"] = None
        if entry["cost"]["status"] != "measured":
            entry["cost"]["observed"] = None

    return {
        "run_id": receipt.run_id,
        "case_id": receipt.case_id,
        "considered": len(receipt.considered),
        "spawned": len(receipt.spawned),
        "skipped": len(receipt.skipped),
        "deferred": len(receipt.deferred),
        "agents": per_agent,
        "waste": agent_waste(receipt),
        "handoffs": [h.to_dict() for h in receipt.handoffs],
        "budgets": {k: dict(v) for k, v in receipt.budgets.items()},
    }


__all__ = [
    "AGENT_WASTE_PATTERNS",
    "SPAN_OUTCOMES",
    "AgentExecutionReceipt",
    "AgentSpan",
    "CandidateRecord",
    "HandoffRecord",
    "agent_value_report",
    "agent_waste",
]


def spans_from_execution(receipt: Any) -> list[AgentSpan]:
    """§122 — runtime receipts -> AgentSpan lanes.

    Converte ``execution.AgentExecutionReceipt`` (o recibo de execucao de
    runtime) em spans: runtime, execution_mode, spawn_id, output validity,
    duracao e handoffs viram campos medidos — nunca inferidos de prosa.
    """
    spans: list[AgentSpan] = []
    sent: dict[str, int] = {}
    recv: dict[str, int] = {}
    for h in receipt.state.handoffs:
        sent[h["sender"]] = sent.get(h["sender"], 0) + 1
        recv[h["receiver"]] = recv.get(h["receiver"], 0) + 1
    for stage in receipt.stages:
        res = stage.spawn_result
        if res is None:
            continue
        out = res.structured_output or {}
        facts = len(out.get("proposed_findings") or out.get("facts") or [])
        unresolved = out.get("unresolved") or []
        outcome = (
            "ok" if res.status == "completed" and not stage.schema_violations
            else "blocked" if res.status == "unresolved"
            else "error"
        )
        span = AgentSpan(
            agent_id=stage.agent_id,
            family=str(res.runtime),
            case_id=receipt.case_id,
            run_id=receipt.fingerprint,
            spawn_reason=stage.spawn_reason,
            spawn_trigger=res.execution_mode,
            started_at=res.started,
            ended_at=res.completed,
            stop_reason=res.error or "",
            outcome=outcome,
            facts_emitted=facts,
            unresolved_resolved=len(
                [u for u in unresolved if "resolved" in str(u)]),
            handoffs_sent=sent.get(stage.agent_id, 0),
            handoffs_received=recv.get(stage.agent_id, 0),
            runtime=str(res.runtime),
            execution_mode=res.execution_mode,
            runtime_spawn_id=res.spawn_id,
            output_valid=not stage.schema_violations,
        )
        spans.append(span)
    return spans
