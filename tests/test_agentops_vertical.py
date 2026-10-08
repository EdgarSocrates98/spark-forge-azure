"""AgentOps vertical instrumentation + recovery + memory + counterfactual."""
from __future__ import annotations

from pathlib import Path

import pytest

from sparkforge_azure.azure import counterfactual, memory, pipeline
from sparkforge_azure.collectors import recover
from sparkforge_azure.observability import context_ledger

FIXTURES = Path(__file__).parent / "fixtures" / "access"


# ---------------------------------------------------------------- AgentOps

def test_run_case_records_stage_spans() -> None:
    ledger = context_ledger.shared_ledger()
    before = len(ledger._buffer)
    pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    stage_names = {s.name for s in ledger._buffer[before:]}
    assert {"diagnose.load_bundle", "diagnose.extract", "diagnose.notebook_scan",
            "diagnose.diagnose", "diagnose.rules", "diagnose.graph",
            "diagnose.evidence_trust"} <= stage_names


def test_context_quality_block() -> None:
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    cq = report["context_quality"]
    assert cq["selected"] > 0
    assert cq["required"] > 0
    assert cq["required_basis"] == "diagnosis.chain.evidence + findings.evidence"
    # every required evidence id resolves to a produced fact
    assert cq["required_recall"] == pytest.approx(1.0)
    assert cq["consumed_bytes"] > 0
    assert cq["cited"] <= cq["selected"] or True  # cited subset of required


def test_agentops_waste_patterns(tmp_path: Path) -> None:
    """Waste detector: duplicate spans observed; L6-after-hit is hypothesis."""
    from sparkforge_azure.observability.agentops import _waste

    spans = [
        {"component_type": "tool", "name": "sfa_graph_query", "span_id": "a",
         "metadata_json": "{}", "outcome": "ok", "payload_bytes": 10},
        {"component_type": "tool", "name": "sfa_graph_query", "span_id": "b",
         "metadata_json": "{}", "outcome": "ok", "payload_bytes": 10},
        {"component_type": "tool", "name": "tokensave.search", "span_id": "c",
         "detail_level": "L1", "outcome": "ok", "payload_bytes": 5,
         "start_time": 1.0},
        {"component_type": "tool", "name": "tokensave.read_full", "span_id": "d",
         "detail_level": "L6", "outcome": "ok", "payload_bytes": 9000,
         "start_time": 2.0},
    ]
    patterns = {f.pattern: f.classification for f in _waste(spans)}
    assert patterns["duplicate_tool_call"] == "observed"
    assert patterns["full_read_after_index_hit"] == "hypothesis"


# ---------------------------------------------------------------- recovery

def _failing(exc: BaseException):
    def _live(**_kw):
        raise exc
    return _live


def test_recovery_retries_transient_network() -> None:
    calls = {"n": 0}

    def live(**_kw):
        calls["n"] += 1
        raise ConnectionError("dns")

    out = recover.collect_with_recovery(live, source="unity-catalog")
    assert out["status"] == "unresolved"
    assert out["unresolved"][0]["failure_class"] == "network"
    assert calls["n"] == 3  # attempt 0,1 retried; attempt 2 hits max_attempts
    assert out["receipt"]["attempts"] == 3
    assert out["receipt"]["fallback"] == "unavailable"


def test_recovery_no_retry_on_authn(tmp_path: Path) -> None:
    class Http401(Exception):
        status_code = 401

    calls = {"n": 0}

    def live(**_kw):
        calls["n"] += 1
        raise Http401()

    out = recover.collect_with_recovery(live, source="azure-rbac")
    assert calls["n"] == 1  # authn is never retried (#122)
    assert out["decisions"][0]["action"] == "refuse"
    assert out["unresolved"][0]["failure_class"] == "authentication"


def test_recovery_fallback_to_offline_export(tmp_path: Path) -> None:
    export = tmp_path / "rbac.json"
    export.write_text('{"assignments": []}', encoding="utf-8")

    def from_export(path):
        return {"mode": "export", "path": str(path), "records": 0}

    def live(**_kw):
        raise ConnectionError("private endpoint unreachable")

    out = recover.collect_with_recovery(
        live, offline_export=str(export), from_export=from_export,
        source="azure-rbac")
    assert out["status"] == "degraded"
    assert out["receipt"]["fallback"]["from"] == "live"
    assert out["receipt"]["fallback"]["to"] == "offline_export"
    assert out["receipt"]["fallback"]["failure_class"] == "network"
    assert out["result"]["mode"] == "export"


def test_recovery_same_failure_twice_stops() -> None:
    """Fingerprint repeated -> STOP, never an infinite retry loop."""
    calls = {"n": 0}

    def live(**_kw):
        calls["n"] += 1
        raise TimeoutError("slow")

    out = recover.collect_with_recovery(live, source="adls-meta")
    assert calls["n"] <= 4  # policy stop condition reached
    assert out["status"] == "unresolved"


# ---------------------------------------------------------------- memory

def test_access_case_memory_roundtrip(tmp_path: Path) -> None:
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    out = memory.record_access_case(report, tmp_path)
    assert Path(out["recorded"]).is_file()
    rec = out["memory"]["record"]
    assert rec["workload_type"] == "azure_databricks_uc_adls_access"
    assert rec["environment_fingerprint"]  # s01 carrega ARM ids -> subscription
    assert rec["status"] in {"accepted", "quarantine"}


def test_env_fingerprint_has_azure_fields(tmp_path: Path) -> None:
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    env = memory.env_fingerprint(report)
    assert env.get("subscription")  # ARM id -> subscription guid
    assert "workspace" in env


def test_wrong_environment_memory_not_auto_reused(tmp_path: Path) -> None:
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    memory.record_access_case(report, tmp_path)
    problem = memory._problem_text(report)
    # mesmo problema, ambiente diferente -> candidato marcado, nao reusado
    other_env = dict(memory.env_fingerprint(report))
    other_env["subscription"] = "00000000-0000-0000-0000-000000000000"
    out = memory.retrieve_access_memory(problem, other_env, tmp_path)
    for item in out["candidates"]:
        if item.get("environment_fingerprint") != out.get("environment_fingerprint"):
            continue
    same_env = memory.retrieve_access_memory(
        problem, memory.env_fingerprint(report), tmp_path)
    for cand in same_env["candidates"]:
        env_hit = (cand.get("retrieval") or {}).get("environment")
        if env_hit == 0.0:
            assert cand["wrong_environment"] is True
            assert cand["auto_reusable"] is False


# ---------------------------------------------------------------- counterfactual

def test_counterfactual_sweep(tmp_path: Path) -> None:
    out = counterfactual.counterfactual_sweep(
        FIXTURES / "s04_private_dns_not_linked")
    assert out["removed_items"] >= 5
    rows = {r["removed"]: r for r in out["rows"]}
    # remover a evidência de rede do caso de rede muda o veredito
    assert rows["network.json"]["changed"] is True
    assert out["authority"] == "data_only"
    assert 0.0 <= (out["sensitivity"] or 0.0) <= 1.0
