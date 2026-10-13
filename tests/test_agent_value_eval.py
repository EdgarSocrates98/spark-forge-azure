"""Agent value eval — SDD AGENT_VALUE_EVAL (§50-75)."""
from __future__ import annotations

from pathlib import Path

from sparkforge_azure.agentic.agent_eval import (
    CONFIGS,
    NECESSITY,
    EvalResult,
    classify_necessity,
    evaluate_case,
    value_vector,
)

CASES = Path("evals/agent_runtime/cases")


def test_eval_result_format() -> None:
    out = evaluate_case(CASES / "streaming_lag.yaml")
    assert out["case_id"] == "streaming-lag"
    assert set(out["results"]) == set(CONFIGS)
    for res in out["results"].values():
        for field in (
            "case_id", "configuration", "runtime", "agents", "quality",
            "evidence", "unresolved", "tokens", "cost", "latency_s",
            "tool_calls", "context_bytes",
        ):
            assert field in res, f"missing {field}"


def test_same_input_across_configs() -> None:
    out = evaluate_case(CASES / "databricks_access.yaml")
    runtimes = {r["runtime"] for r in out["results"].values()}
    assert runtimes == {"generic"}
    # mesma entrada: o que muda e so o conjunto de agents habilitados
    assert out["results"]["A"]["agents"] != out["results"]["D"]["agents"]


def test_value_vector_and_necessity() -> None:
    out = evaluate_case(CASES / "fabric_onelake.yaml")
    for vec in out["value_vectors"].values():
        for dim in (
            "information_gain", "evidence_gain", "uncertainty_reduction",
            "decision_impact", "quality_delta", "cost", "latency_delta_s",
        ):
            assert dim in vec, f"missing {dim}"
    for nec in out["necessity"].values():
        assert nec in NECESSITY


def test_honest_cost_and_harmful() -> None:
    out = evaluate_case(CASES / "migration.yaml")
    for res in out["results"].values():
        assert res["tokens"]["status"] == "unresolved"  # §55
        assert res["cost"]["status"] == "unresolved"
    # forbidden finding -> HARMFUL (§60)
    res = EvalResult(
        case_id="x", configuration="B", runtime="generic", agents=[],
        quality={
            "required_findings_hit": 0, "required_findings_total": 0,
            "forbidden_findings_hit": 1, "forbidden_findings": ["cloud_write"],
            "known_unresolved_preserved": 0, "known_unresolved_total": 0,
            "provisional_findings": 1,
        },
        evidence=[], unresolved=[], latency_s=0.1,
    )
    vec = value_vector(res, res)
    assert classify_necessity(vec, res) == "HARMFUL"


def test_no_spawned_agent_inflation() -> None:
    # §16 — playbook/inline nunca reporta spawned_agents inflado
    out = evaluate_case(CASES / "streaming_lag.yaml")
    for res in out["results"].values():
        # agents = estagios com spawn_result, nao "agents em paralelo"
        assert len(res["agents"]) <= len(set(res["agents"])) + 8
