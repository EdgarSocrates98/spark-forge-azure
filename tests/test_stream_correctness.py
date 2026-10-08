"""SDD STREAMING_CORRECTNESS — delivery semantics are unresolved-first."""
from __future__ import annotations

from sparkforge_azure.stream import correctness, extract
from sparkforge_azure.stream.casefile import load_bundle
from sparkforge_azure.stream.pipeline import run_stream_case

FIXTURES = "tests/fixtures/stream"


def _facts(case: str):
    b = load_bundle(f"{FIXTURES}/{case}")
    return extract.extract_all(b.artifacts, b.sources)


def test_no_evidence_is_unresolved_never_exactly_once():
    d = correctness.classify_delivery(_facts("s22-insufficient-evidence"))
    assert d["classification"] == "unresolved"
    assert d["classification"] != "exactly_once_claim_supported"


def test_checkpoint_deleted_latest_is_at_most_once_possible():
    d = correctness.classify_delivery(_facts("s08-checkpoint-deleted-latest"))
    assert d["classification"] == "at_most_once_possible"


def test_at_least_once_when_sink_not_idempotent():
    d = correctness.classify_delivery(_facts("s01-caught-up-idle"))
    assert d["classification"] in {"at_least_once", "effectively_once",
                                   "exactly_once_claim_supported"}
    # never claims exactly-once without transactional+idempotent+sync evidence
    if d["classification"] == "exactly_once_claim_supported":
        sink = [f for f in _facts("s01-caught-up-idle")
                if f.kind == "stream.sink"]
        assert any(f.attrs.get("transactional") and
                   (f.attrs.get("idempotent") or f.attrs.get("merge_keys"))
                   for f in sink)


def test_schema_additive_is_compatible():
    c = correctness.schema_compatibility(_facts("s12-schema-additive"))
    assert c["verdict"] == "compatible"


def test_schema_breaking_detected():
    c = correctness.schema_compatibility(_facts("s13-schema-breaking"))
    assert c["verdict"] == "breaking"
    assert c["changes"]


def test_retention_loss_candidate_is_risk_not_fact():
    cands = correctness.data_loss_candidates(
        _facts("s09-checkpoint-behind-retention"))
    kinds = {c["kind"] for c in cands}
    assert "checkpoint_older_than_retention" in kinds
    for c in cands:
        assert "RISCO" in c["explanation"].upper() or "risk" in c[
            "explanation"].lower() or "impossível" in c["explanation"]


def test_delivery_in_pipeline_output():
    r = run_stream_case(f"{FIXTURES}/s01-caught-up-idle")
    assert r["delivery"]["classification"] in correctness.DELIVERY_ORDER


def test_delivery_classification():
    """SDD contract name — classificação é sempre uma de DELIVERY_ORDER."""
    for case in ("s01-caught-up-idle", "s08-checkpoint-deleted-latest",
                 "s22-insufficient-evidence"):
        d = correctness.classify_delivery(_facts(case))
        assert d["classification"] in correctness.DELIVERY_ORDER, case


def test_schema_breaking_vs_additive():
    """AC2 — additive nullable passa; type change quebra."""
    assert correctness.schema_compatibility(
        _facts("s12-schema-additive"))["verdict"] == "compatible"
    assert correctness.schema_compatibility(
        _facts("s13-schema-breaking"))["verdict"] == "breaking"


def test_no_data_loss_needs_full_evidence():
    """AC3 — 'sem perda' exige evidência completa; ausência = unresolved."""
    r = run_stream_case(f"{FIXTURES}/s22-insufficient-evidence")
    assert r["status"] == "unresolved"
    assert r["delivery"]["classification"] == "unresolved"


def test_payload_data_only():
    """AC4 — payload hostil é DATA_ONLY: não vira finding nem verdict."""
    r = run_stream_case(f"{FIXTURES}/s21-malicious-payload")
    assert r["trust"]["instruction_authority"] == "data_only"
    assert not any("malicious" in f["title"].lower() for f in r["findings"])
