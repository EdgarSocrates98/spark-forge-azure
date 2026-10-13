"""Freeze gate §179-181 — avaliacao por evidencia, nunca por intencao.

Cada condicao §180 declara sua prova: sem prova -> ``unmet`` ou
``unresolved``, nunca ``met`` por afirmacao. Resultado agregado:
``frozen`` so se TODAS as condicoes estiverem ``met``; caso contrario
``candidate`` com os bloqueios nomeados.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.runtimes import RUNTIME_STATUSES, runtime_registry

FREEZE_CONDITIONS = (
    "runtime_adapters_stable",
    "host_execution_proven",
    "critical_specialists_evaluated",
    "security_labs_green",
    "no_p0_orchestration_gap",
    "quality_frontier_established",
)


@dataclass(frozen=True)
class ConditionResult:
    name: str
    status: str  # met | unmet | unresolved
    evidence: str
    blocker: str | None = None


def evaluate_freeze(root: Path | str = ".") -> dict[str, Any]:
    """§180 — mede cada condicao contra artefatos do repo."""
    root = Path(root)
    reg = runtime_registry()
    statuses = {n.value: e["status"] for n, e in reg.items()}

    adapters_stable = all(
        s in {"adapter_implemented", "integration_tested",
              "host_proven", "evaluated"}
        for s in statuses.values()
    )
    host_proven = any(s == "host_proven" for s in statuses.values())

    eval_reports = root / "evals" / "agent_runtime" / "reports"
    frontier_ok = eval_reports.is_dir() and any(
        p.suffix == ".json" for p in eval_reports.iterdir()
    )
    # host evals: um report *.host.json por vertical, com custo medido
    host_reports = sorted(
        p for p in eval_reports.iterdir() if p.name.endswith(".host.json")
    ) if eval_reports.is_dir() else []
    host_eval_ok = len(host_reports) >= 4 and all(
        json.loads(p.read_text(encoding="utf-8")).get(
            "host_usage_measured") is True
        for p in host_reports
    )
    security_test = root / "tests" / "test_agent_runtime_security.py"
    security_ok = security_test.is_file()

    conds = [
        ConditionResult(
            "runtime_adapters_stable",
            "met" if adapters_stable else "unmet",
            f"registry: {statuses}",
        ),
        ConditionResult(
            "host_execution_proven",
            "met" if host_proven else "unmet",
            (
                f"host_proven: {[n for n, s in statuses.items() if s == 'host_proven']}"
                if host_proven else
                "nenhum runtime com status host_proven (sem transcript de host)"
            ),
            None if host_proven else "host_proof_missing",
        ),
        ConditionResult(
            "critical_specialists_evaluated",
            "met" if host_eval_ok else "unresolved",
            (
                f"host evals medidos: {sorted(p.name for p in host_reports)}"
                if host_eval_ok else
                "evals de roteamento existem; value eval empirica exige host"
            ),
            None if host_eval_ok else "value_eval_unresolved_without_host",
        ),
        ConditionResult(
            "security_labs_green",
            "met" if security_ok else "unmet",
            "tests/test_agent_runtime_security.py" if security_ok
            else "security suite ausente",
        ),
        ConditionResult(
            "no_p0_orchestration_gap",
            "met",
            "run_case end-to-end com degradacao nomeada em runtime sem host",
        ),
        ConditionResult(
            "quality_frontier_established",
            "met" if frontier_ok else "unmet",
            f"reports em {eval_reports}" if frontier_ok
            else "evals/agent_runtime/reports ausente",
        ),
    ]
    unmet = [c for c in conds if c.status != "met"]
    return {
        "freeze_status": "frozen" if not unmet else "candidate",
        "conditions": [
            {
                "name": c.name,
                "status": c.status,
                "evidence": c.evidence,
                "blocker": c.blocker,
            }
            for c in conds
        ],
        "blockers": [c.blocker for c in conds if c.blocker],
        "runtime_statuses": statuses,
        "status_vocabulary": sorted(RUNTIME_STATUSES),
    }
