"""Engine de execucao canonica (§24-38, §45-48).

    Case -> deterministic core -> routing -> spawn gate -> adapter
         -> structured/provisional result -> schema validation
         -> AgentExecutionReceipt (§28)

O shell e deterministico; so o centro probabilistico (specialist,
reviewer...) depende de host (§94-95). Sem host provado, esses estagios
voltam ``unresolved`` nomeado — o case continua, degradado e explicito
(§78-80), nunca finge (§79).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.autonomy import autonomy_for
from sparkforge_azure.agentic.pipeline import plan_pipeline
from sparkforge_azure.agentic.runtime import RuntimeName
from sparkforge_azure.agentic.runtimes import (
    AgentSpawnRequestV2,
    AgentSpawnResultV2,
    get_adapter,
)
from sparkforge_azure.agentic.runtimes.base import fingerprint_of
from sparkforge_azure.agentic.schemas import parse_freeform, validate_output
from sparkforge_azure.agentic.spawn import SpawnContext, decide_spawn
from sparkforge_azure.agentmanifest.model import parse_manifest
from sparkforge_azure.agentmanifest.routing import route

# §200 — falha de um estagio nao derruba o case; degrade e registre.
_DEGRADED = "degraded"


@dataclass(frozen=True)
class AgentExecutionRecord:
    """Um estagio executado: gate + spawn + validacao, com recibo."""

    agent_id: str
    spawn_decision: str
    spawn_reason: str
    spawn_result: AgentSpawnResultV2 | None
    schema_violations: tuple[str, ...] = ()
    duration_s: float | None = None

    @property
    def executed(self) -> bool:
        return self.spawn_result is not None and self.spawn_result.status in {
            "completed", "unresolved",
        }


@dataclass
class CaseState:
    """§45 — estado acumulado do case durante a execucao."""

    agents_considered: list[str] = field(default_factory=list)
    agents_spawned: list[str] = field(default_factory=list)
    agents_completed: list[str] = field(default_factory=list)
    agents_degraded: list[str] = field(default_factory=list)
    handoffs: list[dict[str, Any]] = field(default_factory=list)
    provisional_findings: list[str] = field(default_factory=list)
    verified_findings: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    budgets: dict[str, int | None] = field(default_factory=dict)


@dataclass
class AgentExecutionReceipt:
    """§28 + §48 — recibo do run: por que rodou, como, com que evidencia."""

    case_id: str
    runtime: str
    fingerprint: str
    stages: list[AgentExecutionRecord]
    state: CaseState
    degraded: bool = False
    degraded_reasons: list[str] = field(default_factory=list)
    started: float = 0.0
    completed: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "runtime": self.runtime,
            "fingerprint": self.fingerprint,
            "degraded": self.degraded,
            "degraded_reasons": self.degraded_reasons,
            "state": {
                "agents_considered": self.state.agents_considered,
                "agents_spawned": self.state.agents_spawned,
                "agents_completed": self.state.agents_completed,
                "agents_degraded": self.state.agents_degraded,
                "provisional_findings": self.state.provisional_findings,
                "verified_findings": self.state.verified_findings,
                "conflicts": self.state.conflicts,
                "unresolved": self.state.unresolved,
            },
            "stages": [
                {
                    "agent_id": s.agent_id,
                    "spawn_decision": s.spawn_decision,
                    "spawn_reason": s.spawn_reason,
                    "status": s.spawn_result.status if s.spawn_result else None,
                    "execution_mode": (
                        s.spawn_result.execution_mode if s.spawn_result else None
                    ),
                    "schema_violations": list(s.schema_violations),
                    "duration_s": s.duration_s,
                }
                for s in self.stages
            ],
            "started": self.started,
            "completed": self.completed,
        }


def _spawn_request(
    agent_id: str, case: dict[str, Any], root: Path | str
) -> AgentSpawnRequestV2:
    """§25-26 — resolve manifest contract antes do spawn."""
    data = parse_manifest(Path(root) / "agents" / f"{agent_id}.md").data
    return AgentSpawnRequestV2(
        agent_id=agent_id,
        task=str(case.get("task") or case.get("query") or agent_id),
        context=dict(case.get("context") or {}),
        context_refs=tuple(case.get("context_refs") or ()),
        allowed_tools=tuple(data.get("allowed_tools") or ()),
        budget_tokens=case.get("budget_tokens"),
        timeout_seconds=int(case.get("timeout_seconds") or 120),
        autonomy=autonomy_for(agent_id, root).value,
        case_fingerprint=str(case.get("fingerprint") or ""),
    )


def run_case(
    case: dict[str, Any],
    *,
    runtime: RuntimeName | str = RuntimeName.GENERIC,
    root: Path | str = ".",
    max_specialists: int = 2,
) -> AgentExecutionReceipt:
    """Executa o fluxo canonico §24 sobre um case.

    ``case`` e DATA: {id?, task|query, context?, unresolved?, findings?,
    conflicts?, evidence_complete?, low_risk?, needs_review?,
    needs_referee?}.
    """
    rt = runtime if isinstance(runtime, RuntimeName) else RuntimeName(runtime)
    adapter = get_adapter(rt)
    started = time.time()
    state = CaseState(
        unresolved=list(case.get("unresolved") or []),
        conflicts=list(case.get("conflicts") or []),
    )
    query = str(case.get("task") or case.get("query") or "")
    specialists = route(query, max_agents=max_specialists) if query else []

    stages_plan: list[str] = []
    for spec in specialists:
        stages_plan.extend(
            plan_pipeline(
                specialist_id=spec,
                needs_review=bool(case.get("needs_review")),
                has_conflict=bool(case.get("conflicts")),
                needs_referee=bool(case.get("needs_referee")),
                evidence_complete=bool(case.get("evidence_complete")),
                low_risk=bool(case.get("low_risk")),
            )
        )
    # dedup preservando ordem (specialists repetem a espinha)
    seen: set[str] = set()
    pipeline = [s for s in stages_plan if not (s in seen or seen.add(s))]

    ctx = SpawnContext(
        routed_specialists=tuple(specialists),
        unresolved=tuple(state.unresolved),
        findings=tuple(case.get("findings") or ()),
        conflicts=tuple(state.conflicts),
        gate_requested=bool(case.get("gate_requested")),
    )

    records: list[AgentExecutionRecord] = []
    degraded_reasons: list[str] = []
    for agent_id in pipeline:
        state.agents_considered.append(agent_id)
        decision = decide_spawn(agent_id, ctx, root=root)
        if decision.decision != "SPAWN":
            records.append(AgentExecutionRecord(
                agent_id, decision.decision, decision.reason, None))
            continue
        request = _spawn_request(agent_id, case, root)
        state.agents_spawned.append(agent_id)
        state.budgets[agent_id] = request.budget_tokens
        result = adapter.spawn_agent(request)
        violations: list[str] = []
        if result.status == "completed":
            if result.structured_output is None:
                # §31 — freeform do host vira provisional, nunca verified
                result.structured_output = parse_freeform(agent_id, result.output)
            violations = validate_output(agent_id, result.structured_output)
            if violations:
                degraded_reasons.append(f"{agent_id}:contract_violation")
                state.agents_degraded.append(agent_id)
            else:
                state.agents_completed.append(agent_id)
                _absorb(agent_id, result.structured_output, state)
        elif result.status == "unresolved":
            state.agents_completed.append(agent_id)
            state.agents_degraded.append(agent_id)
            reason = (
                result.structured_output.get("unresolved")
                if result.structured_output else "unresolved"
            )
            state.unresolved.append(f"{agent_id}:{reason}")
            degraded_reasons.append(f"{agent_id}:{_DEGRADED}:{reason}")
        else:
            kind = result.failure_kind() or "spawn_failed"
            state.agents_degraded.append(agent_id)
            degraded_reasons.append(f"{agent_id}:{kind}")
        records.append(AgentExecutionRecord(
            agent_id,
            decision.decision,
            decision.reason,
            result,
            tuple(violations),
            result.duration_s,
        ))

    return AgentExecutionReceipt(
        case_id=str(case.get("id") or "case"),
        runtime=rt.value,
        fingerprint=fingerprint_of({
            "case": str(case.get("id") or query),
            "pipeline": pipeline,
            "runtime": rt.value,
        }),
        stages=records,
        state=state,
        degraded=bool(degraded_reasons),
        degraded_reasons=degraded_reasons,
        started=started,
        completed=time.time(),
    )


def _absorb(agent_id: str, out: dict[str, Any], state: CaseState) -> None:
    """Provisional findings entram no estado — nunca verified (§32)."""
    for f in out.get("proposed_findings") or out.get("facts") or []:
        state.provisional_findings.append(f"{agent_id}:{f}")
    for u in out.get("unresolved") or []:
        state.unresolved.append(f"{agent_id}:{u}")
    for c in out.get("conflicts") or []:
        state.conflicts.append(f"{agent_id}:{c}")
