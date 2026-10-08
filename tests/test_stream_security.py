"""Cycle 4 security wave — taint, redaction, no payload exfiltration."""
from __future__ import annotations

import json

from sparkforge_azure.stream import extract
from sparkforge_azure.stream.casefile import load_bundle
from sparkforge_azure.stream.pipeline import run_stream_case

FIXTURES = "tests/fixtures/stream"


def test_malicious_payload_case_is_external_taint():
    r = run_stream_case(f"{FIXTURES}/s21-malicious-payload")
    assert r["trust"]["taint"] == "external"
    assert r["trust"]["instruction_authority"] == "data_only"


def test_no_raw_event_payloads_in_report():
    r = run_stream_case(f"{FIXTURES}/s21-malicious-payload")
    blob = json.dumps(r).lower()
    for needle in ("drop table", "'; delete", "<script", "powershell"):
        assert needle not in blob, needle


def test_connection_strings_redacted_at_boundary():
    """A SAS connection string in eventhubs.json never reaches a fact."""
    b = load_bundle(f"{FIXTURES}/s15-eventstream-source-auth")
    facts = extract.extract_all(b.artifacts, b.sources)
    blob = json.dumps([f.to_dict() for f in facts])
    assert "SharedAccessKey=" not in blob
    assert "Endpoint=sb://" not in blob or "[REDACTED" in blob


def test_untrusted_events_never_drive_verdict():
    """sample_events is DATA_ONLY: hostile content cannot flip a verdict."""
    r = run_stream_case(f"{FIXTURES}/s21-malicious-payload")
    assert r["status"] == "pass"  # metadata healthy; payload is data
    assert r["failure_layer"] is None


def test_environment_fingerprint_present():
    r = run_stream_case(f"{FIXTURES}/s04-eh-throttled")
    fp = r["case_meta"]["environment_fingerprint"]
    assert fp and isinstance(fp, dict)
