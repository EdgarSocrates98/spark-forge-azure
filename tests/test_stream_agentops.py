"""SDD STREAMING_ECONOMY_OBSERVABILITY — AgentOps stream.* stage spans."""
from __future__ import annotations

from sparkforge_azure.stream.pipeline import run_stream_case

FIXTURES = "tests/fixtures/stream"


def test_stream_stage_spans(tmp_path, monkeypatch):
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    run_stream_case(f"{FIXTURES}/s04-eh-throttled")
    from sparkforge_azure.observability.context_ledger import shared_ledger
    led = shared_ledger()
    spans = [s.to_dict() for s in led._buffer
             if s.to_dict().get("name", "").startswith("stream.")]
    names = {s["name"] for s in spans}
    for stage in ("stream.load_case", "stream.extract", "stream.diagnose",
                  "stream.graph", "stream.rules", "stream.evidence_trust"):
        assert stage in names, names
    for s in spans:
        assert s["outcome"] == "ok"


def test_report_stage_overhead_is_stream_prefixed(tmp_path, monkeypatch):
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(tmp_path / "state"))
    r = run_stream_case(f"{FIXTURES}/s04-eh-throttled")
    assert set(r["overhead"]["stages"]) >= {
        "load_case", "extract", "diagnose", "graph"}
    assert all(v["ms"] >= 0 for v in r["overhead"]["stages"].values())


def test_receipt_records_sources_and_counts():
    r = run_stream_case(f"{FIXTURES}/s04-eh-throttled")
    receipt = r["receipt"]
    assert receipt["sources"]
    assert receipt["facts"] > 0
