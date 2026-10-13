"""SDD FABRIC_GRAPH_TOKENSAVE — AgentOps fabric.* stage spans."""
from __future__ import annotations

from sparkforge_azure.fabric.pipeline import run_fabric_case

FIXTURES = "tests/fixtures/fabric"


def test_fabric_stage_spans(tmp_path, monkeypatch):
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    run_fabric_case(f"{FIXTURES}/f02_onelake_denied")
    from sparkforge_azure.observability.context_ledger import shared_ledger
    led = shared_ledger()
    spans = [s.to_dict() for s in led._buffer
             if s.to_dict().get("name", "").startswith("fabric.")]
    names = {s["name"] for s in spans}
    for stage in ("fabric.load_case", "fabric.extract", "fabric.diagnose",
                  "fabric.graph", "fabric.rules", "fabric.evidence_trust"):
        assert stage in names, names
    for s in spans:
        assert s["outcome"] == "ok"


def test_report_stage_overhead_is_fabric_prefixed(tmp_path, monkeypatch):
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    r = run_fabric_case(f"{FIXTURES}/f02_onelake_denied")
    assert set(r["overhead"]["stages"]) >= {
        "load_case", "extract", "diagnose", "graph"}
    assert all(v["ms"] >= 0 for v in r["overhead"]["stages"].values())
