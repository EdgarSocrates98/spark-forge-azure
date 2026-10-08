"""Closing-criteria wave: live cache freshness, overhead metrics, quality
frontier, env-mismatch, credential redaction at the bundle boundary, and
trust-floor review (prompts 168-169, 182-197).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sparkforge_azure.azure import pipeline
from sparkforge_azure.collectors.cache import LiveCache
from sparkforge_azure.collectors.resource_graph import ResourceGraphCollector
from sparkforge_azure.tokensave.benchmark import run_benchmark

FIXTURES = Path(__file__).parent / "fixtures" / "access"


# -- 168/169: cache keyed by (resource_id, query); stale never current ------

def test_cache_fresh_hit_skips_fetch() -> None:
    clock = iter([1000.0, 1001.0])
    cache = LiveCache(ttl_seconds=60, clock=lambda: next(clock))
    calls = []
    cache.put("res1", "q", ["r1"])
    calls.append(1)  # put consumed one tick
    v, origin = cache.get_or_call("res1", "q", lambda: calls.append(1) or ["r2"])
    assert (v, origin) == (["r1"], "fresh")
    assert calls == [1]  # fetch never ran


def test_cache_stale_past_ttl_refetches_by_default() -> None:
    t = [0.0]
    cache = LiveCache(ttl_seconds=10, clock=lambda: t[0])
    cache.put("res", "q", "old")
    t[0] = 999.0
    v, origin = cache.get_or_call("res", "q", lambda: "new")
    assert (v, origin) == ("new", "live")


def test_cache_stale_visible_only_when_allowed() -> None:
    t = [0.0]
    cache = LiveCache(ttl_seconds=10, clock=lambda: t[0])
    cache.put("res", "q", "old")
    t[0] = 999.0
    v, origin = cache.get_or_call("res", "q", lambda: "new", allow_stale=True)
    assert (v, origin) == ("old", "stale")
    hit = cache.get("res", "q")
    assert hit is not None and hit.freshness == "stale" and hit.age_seconds == 999.0


def test_resource_graph_collector_marks_stale_cache_in_unresolved() -> None:
    class _Resp:
        data = [{"id": "/subscriptions/00000000-0000-0000-0000-000000000001/"
                         "resourceGroups/rg/providers/Microsoft.Storage/"
                         "storageAccounts/stg", "name": "stg"}]
        skip_token = None

    class _Client:
        def __init__(self) -> None:
            self.calls = 0

        def resources(self, req):
            self.calls += 1
            return _Resp()

    t = [0.0]
    cache = LiveCache(ttl_seconds=10, clock=lambda: t[0])
    client = _Client()
    c = ResourceGraphCollector(["00000000-0000-0000-0000-000000000001"],
                               client=client, cache=cache, allow_stale=True,
                               request_builder=lambda *a: object())
    r1 = c.collect()
    assert not any(u["reason"] == "cache_stale" for u in r1.unresolved)
    t[0] = 9999.0
    r2 = c.collect()  # stale hit allowed — visible in unresolved
    stale = [u for u in r2.unresolved if u["reason"] == "cache_stale"]
    assert stale and stale[0]["cache_age_seconds"] == 9999.0


# -- 182/183: overhead -------------------------------------------------------

def test_report_records_graph_overhead() -> None:
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    oh = report["overhead"]["graph"]
    assert oh["nodes"] > 0 and oh["edges"] > 0
    assert oh["build_ms"] >= 0 and oh["serialized_bytes"] > 0


# -- 185/186/187: quality frontier, no magic score ---------------------------

def test_benchmark_reports_frontier_axes(tmp_path: Path) -> None:
    case = Path("evals/token_efficient/access_case")
    if not case.is_dir():
        pytest.skip("access_case corpus not present")
    out = run_benchmark(case)
    frontier = out["frontier"]
    assert frontier["tokens"] == "unresolved"
    assert "score" not in frontier  # nunca score mágico
    for run in out["profiles"].values():
        assert run["required_recall"] is not None
        assert run["latency_ms"] >= 0
        assert run["agent_calls"] == 0
        assert run["calls"] >= 1


# -- 193/194/195: cross-environment evidence ----------------------------------

def _bundle(tmp_path: Path, *, tenant_uc: str, tenant_entra: str) -> Path:
    b = tmp_path / "case"
    b.mkdir()
    (b / "case.yaml").write_text(
        "name: xenv\nprincipal: {id: spn-1, type: service_principal}\n"
        "operation: read\ntarget: {kind: table, table: prod.finance.orders}\n",
        encoding="utf-8")
    (b / "entra.json").write_text(json.dumps({
        "tenant_id": tenant_entra,
        "principals": {"spn-1": {"enabled": True}}}), encoding="utf-8")
    (b / "unity_catalog.json").write_text(json.dumps({
        "tenant_id": tenant_uc, "grants": []}), encoding="utf-8")
    return b


def test_cross_tenant_evidence_is_a_finding_not_a_merge(tmp_path: Path) -> None:
    report = pipeline.run_case(_bundle(tmp_path, tenant_uc="t-a",
                                       tenant_entra="t-b"))
    env_findings = [f for f in report["findings"] if f["rule_id"] == "SF-ACC-013"]
    assert env_findings, "tenant mismatch must surface"
    assert report["failure_layer"] == "cross_environment"
    assert env_findings[0]["measured"]["conflicting_keys"]["tenant_id"] == [
        "t-a", "t-b"]
    env_facts = [f for f in report["facts"] if f["kind"] == "environment.scope"]
    assert {f["attrs"]["value"] for f in env_facts
            if f["attrs"]["key"] == "tenant_id"} == {"t-a", "t-b"}


def test_single_environment_produces_no_mismatch(tmp_path: Path) -> None:
    report = pipeline.run_case(_bundle(tmp_path, tenant_uc="t-a",
                                       tenant_entra="t-a"))
    assert not [f for f in report["findings"] if f["rule_id"] == "SF-ACC-013"]


# -- 192: credential redaction at the bundle boundary -------------------------

SECRETS = {
    "sas": "sig=AAAbbb111%2BfakeSASsignature%3D",
    "client_secret": "ClientSecret=sup3r-fake-value-0001",
    "storage_key": "QUJDRDF=" + "A" * 82 + "==",
    "bearer": "Bearer eyJhbGciOi.fakepayload.fakesignaturevalue",
    "connstring": "DefaultEndpointsProtocol=https;AccountName=stg;"
                  "AccountKey=" + "B" * 86 + "==;EndpointSuffix=core.windows.net",
}


def test_bundle_secrets_never_reach_facts_or_report(tmp_path: Path) -> None:
    b = _bundle(tmp_path, tenant_uc="t-a", tenant_entra="t-a")
    poisoned = dict(SECRETS)
    poisoned["storage_credentials"] = {
        "c": {"identity_id": "mi-1", "comment": SECRETS["connstring"]}}
    (b / "unity_catalog.json").write_text(json.dumps(poisoned),
                                          encoding="utf-8")
    report = pipeline.run_case(b)
    blob = json.dumps(report["facts"]) + json.dumps(report["findings"])
    for marker in ("sup3r-fake-value-0001", "fakeSASsignature",
                   "fakesignaturevalue", "B" * 80):
        assert marker not in blob, f"secret material leaked: {marker[:24]}"
    assert "REDACTED" in blob


# -- 196/197: trust floor ------------------------------------------------------

def test_no_report_producer_elevates_instruction_authority() -> None:
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    assert report["trust"]["instruction_authority"] == "data_only"
    blob = json.dumps(report)
    # nada no relatório pode declarar autoridade de instrução elevada
    for forbidden in ('"authority": "system"', '"authority": "policy"',
                      '"instruction_authority": "system"'):
        assert forbidden not in blob
