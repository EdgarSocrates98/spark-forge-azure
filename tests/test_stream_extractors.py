"""SDD EVENT_HUBS_DEEP — extractor contract: facts, provenance, redaction."""
from __future__ import annotations

import pytest

from sparkforge_azure.stream import extract
from sparkforge_azure.stream.casefile import (
    StreamCaseError,
    load_bundle,
)

FIXTURES = "tests/fixtures/stream"


def _facts(case: str):
    b = load_bundle(f"{FIXTURES}/{case}")
    return extract.extract_all(b.artifacts, b.sources)


def test_eventhubs_facts_carry_provenance():
    facts = _facts("s04-eh-throttled")
    assert facts, "no facts extracted"
    for f in facts:
        assert f.provenance.get("source"), f.id
        assert f.provenance.get("extractor"), f.id
        assert f.provenance.get("mode") == "bundle"


def test_hub_and_partitions_extracted():
    facts = _facts("s04-eh-throttled")
    hubs = [f for f in facts if f.kind == "eh.hub"]
    parts = [f for f in facts if f.kind == "eh.partition"]
    assert hubs and hubs[0].subject.get("hub_id")
    # canonical identity is the id, not the display name
    assert hubs[0].subject["hub_id"] != hubs[0].attrs.get("name")
    assert len(parts) == int(hubs[0].attrs.get("partition_count") or 0)


def test_role_assignments_keep_semantics_not_redacted():
    """`role_assignments` is RBAC evidence, not secret material — the
    redaction boundary must NOT blank role/auth_mode (regression: the
    legacy `authorization` key was treated as SAS authorizationRules)."""
    facts = _facts("s04-eh-throttled")
    authz = [f for f in facts if f.kind == "eh.authz"]
    assert authz
    assert authz[0].attrs.get("role") == "receiver"
    assert "[REDACTED" not in str(authz[0].attrs)


def test_throttle_signal_becomes_fact():
    facts = _facts("s04-eh-throttled")
    thr = [f for f in facts if f.kind == "eh.throttle"]
    assert thr, "throttled_requests>0 must emit eh.throttle"
    assert thr[0].attrs["total"] > 0


def test_missing_artifact_yields_no_facts(tmp_path):
    (tmp_path / "case.yaml").write_text(
        "name: t\nprincipal: {kind: sp}\noperation: consume\n"
        "target: {eventhub_id: ns/h}\n", encoding="utf-8")
    b = load_bundle(tmp_path)
    assert extract.extract_all(b.artifacts, b.sources) == []


def test_bundle_missing_case_rejected(tmp_path):
    with pytest.raises(StreamCaseError):
        load_bundle(tmp_path)


def test_consumer_checkpoints_scoped_by_group():
    facts = _facts("s02-consumer-stalled")
    ck = [f for f in facts if f.kind == "consumer.checkpoint"]
    assert ck
    assert all("consumer_group" in f.subject for f in ck)
