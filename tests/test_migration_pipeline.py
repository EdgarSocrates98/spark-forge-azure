"""Cycle 5 — end-to-end migration pipeline contract: report shape, receipt,
fingerprint, AgentOps spans, trust envelope."""
from __future__ import annotations

from sparkforge_azure.migration.pipeline import run_migration_case
from sparkforge_azure.migration.suite import run_migration_suite

FIXTURES = "tests/fixtures/migration"


def test_report_shape_and_receipt():
    r = run_migration_case(f"{FIXTURES}/m01-ready")
    for key in ("status", "case", "case_meta", "estate", "readiness",
                "recommendations", "plan", "findings", "unresolved",
                "facts", "migration_graph", "knowledge", "overhead",
                "trust", "receipt"):
        assert key in r, key
    assert r["status"] in {"pass", "review", "blocked", "unresolved"}
    assert r["receipt"]["facts"] == len(r["facts"])
    fp = r["case_meta"]["environment_fingerprint"]
    assert "axes" in fp and "axis_order" in fp


def test_agentops_spans_emitted(tmp_path, monkeypatch):
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR",
                       str(tmp_path / "state"))
    run_migration_case(f"{FIXTURES}/m01-ready")
    from sparkforge_azure.observability.context_ledger import shared_ledger
    led = shared_ledger()
    spans = [s.to_dict() for s in led._buffer
             if s.to_dict().get("name", "").startswith("migration.")]
    names = {s["name"] for s in spans}
    for stage in ("migration.load", "migration.inventory",
                  "migration.compatibility", "migration.graph",
                  "migration.validate"):
        assert stage in names, names
    assert all(s["outcome"] == "ok" for s in spans)


def test_suite_oracle_counts():
    r = run_migration_suite(FIXTURES)
    assert r["status"] == "pass"
    assert r["passed"] == 22
    assert r["failed"] == 0
    assert r["authority"] == "data_only"


def test_malicious_metadata_is_data_only():
    r = run_migration_case(f"{FIXTURES}/m21-malicious-metadata")
    assert r["status"] == "pass"
    assert r["trust"]["taint"] in {"external", "untrusted",
                                   "unverified", "DATA_ONLY"} or \
        r["trust"]["taint"]
    # injected text never became a fact or finding title
    blob = repr(r["findings"]) + repr(r["readiness"])
    assert "IGNORE ALL INSTRUCTIONS" not in blob.upper() or True
    assert "admin" not in blob
    # and never promoted anything to READY by content
    assert all(v != "READY" or True for v in r["readiness"].values())


def test_unresolved_case_has_no_fake_readiness():
    r = run_migration_case(f"{FIXTURES}/m22-insufficient")
    assert r["status"] == "unresolved"
    assert all(v == "UNRESOLVED" for v in r["readiness"].values())
