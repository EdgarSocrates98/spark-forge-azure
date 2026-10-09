"""Real host eval — SDD REAL_HOST_EVAL (§50-75, config B em host provado).

Os reports sao artefatos gravados por UMA execucao real via claude_code
(opt-in). Os testes validam o contrato dos artefatos + o shape da funcao
sem chamar o host — execucao real fica em scripts/run_agent_host_eval.py.
"""
from __future__ import annotations

import json
from pathlib import Path

from sparkforge_azure.agentic.agent_eval import NECESSITY

REPORTS = Path("evals/agent_runtime/reports")
EXPECTED = (
    "databricks-access", "fabric-onelake", "migration", "streaming-lag",
)


def _reports() -> dict[str, dict]:
    return {
        p.name.removesuffix(".host.json"): json.loads(
            p.read_text(encoding="utf-8"))
        for p in REPORTS.iterdir() if p.name.endswith(".host.json")
    }


def test_host_eval_report_shape() -> None:
    reports = _reports()
    assert set(reports) == set(EXPECTED)
    for case_id, rep in reports.items():
        for field in (
            "case_id", "runtime", "specialist", "spawn",
            "host_usage_measured", "schema_violations", "result",
            "value_vector_vs_A", "necessity", "baseline_A",
        ):
            assert field in rep, f"{case_id}: missing {field}"
        assert rep["case_id"] == case_id
        assert rep["runtime"] == "claude_code"
        assert rep["specialist"].endswith("-specialist")
        assert rep["spawn"]["status"] == "completed"
        assert str(rep["spawn"]["trace_ref"]).startswith("sha256:")


def test_host_reports_measured_usage() -> None:
    for case_id, rep in _reports().items():
        assert rep["host_usage_measured"] is True, case_id
        tokens = rep["result"]["tokens"]
        cost = rep["result"]["cost"]
        assert tokens["status"] == "measured", case_id
        assert tokens["output"] is not None
        assert cost["status"] == "measured", case_id
        assert cost["usd"] is not None and cost["usd"] > 0
        assert rep["result"]["latency_s"] > 0


def test_host_eval_quality_vector() -> None:
    for case_id, rep in _reports().items():
        vec = rep["value_vector_vs_A"]
        for dim in (
            "information_gain", "evidence_gain", "uncertainty_reduction",
            "decision_impact", "quality_delta", "cost", "latency_delta_s",
        ):
            assert dim in vec, f"{case_id}: missing {dim}"
        assert rep["necessity"] in NECESSITY
        # output do host nunca vira verified sem verificacao (§32)
        assert rep["result"]["quality"]["forbidden_findings_hit"] == 0


def test_freeze_frozen_with_real_evidence() -> None:
    from sparkforge_azure.agentic.freeze import evaluate_freeze

    out = evaluate_freeze()
    by_name = {c["name"]: c for c in out["conditions"]}
    assert by_name["host_execution_proven"]["status"] == "met"
    assert by_name["critical_specialists_evaluated"]["status"] == "met"
    assert out["blockers"] == []
    assert out["freeze_status"] == "frozen"
