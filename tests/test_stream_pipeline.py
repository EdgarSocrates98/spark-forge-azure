"""SDD EVENT_HUBS_DEEP/STRUCTURED_STREAMING — end-to-end offline contract."""
from __future__ import annotations

import pytest

from sparkforge_azure.stream.casefile import StreamCaseError, load_bundle
from sparkforge_azure.stream.pipeline import PUBLIC_LAYERS, run_stream_case
from sparkforge_azure.stream.suite import run_stream_suite

FIXTURES = "tests/fixtures/stream"


def test_pipeline_end_to_end_offline():
    r = run_stream_case(f"{FIXTURES}/s04-eh-throttled")
    for key in ("status", "failure_layer", "diagnosis", "delivery",
                "findings", "unresolved", "facts", "stream_graph",
                "evidence_paths", "knowledge", "overhead",
                "context_quality", "trust", "receipt"):
        assert key in r, key
    for stage in ("load_case", "extract", "notebook_scan", "diagnose",
                  "rules", "graph", "evidence_trust"):
        assert stage in r["overhead"]["stages"], stage


def test_suite_all_cases():
    r = run_stream_suite(FIXTURES)
    assert r["failed"] == 0, [c["case"] for c in r["cases"]
                             if c["verdict"] == "fail"]
    assert r["passed"] >= 22


def test_unknown_never_assumed():
    r = run_stream_case(f"{FIXTURES}/s22-insufficient-evidence")
    assert r["status"] == "unresolved"
    assert r["failure_layer"] == "unresolved"
    assert r["unresolved"]
    for u in r["unresolved"]:
        assert "artifact" in u  # names the artifact that would close it


def test_throttled_namespace_is_capacity_layer():
    r = run_stream_case(f"{FIXTURES}/s04-eh-throttled")
    assert r["failure_layer"] == "event_hubs_capacity"


def test_healthy_case_passes_without_findings():
    r = run_stream_case(f"{FIXTURES}/s01-caught-up-idle")
    assert r["status"] == "pass"
    assert r["failure_layer"] is None


def test_public_layers_cover_chain():
    required = {"event_hubs_auth", "event_hubs_network",
                "event_hubs_capacity", "partitioning", "consumer_group",
                "consumer_progress", "checkpoint", "state_store",
                "schema", "spark_processing", "sink",
                "eventstream_source", "eventstream_transform",
                "eventstream_destination", "eventstream_publish",
                "eventhouse_ingestion", "kql", "activator_mapping",
                "activator_evaluation", "cross_environment"}
    assert required <= set(PUBLIC_LAYERS)


def test_findings_never_escape_raw_payloads():
    """s21 ships hostile payloads — the report must carry summaries/refs,
    never the payload text itself (DATA_ONLY boundary)."""
    import json
    r = run_stream_case(f"{FIXTURES}/s21-malicious-payload")
    blob = json.dumps(r).lower()
    for needle in ("drop table", "exec(", "powershell -enc"):
        assert needle not in blob, needle


def test_bundle_missing_case_rejected(tmp_path):
    with pytest.raises(StreamCaseError):
        load_bundle(tmp_path)
