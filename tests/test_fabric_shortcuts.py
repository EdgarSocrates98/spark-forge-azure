"""SDD ONELAKE_SECURITY_SHORTCUTS — passthrough vs delegated chains."""
from __future__ import annotations

from sparkforge_azure.fabric.pipeline import run_fabric_case

FIXTURES = "tests/fixtures/fabric"


def _chain(report):
    return {s["layer"]: s for s in report["diagnosis"]["chain"]}


def test_passthrough_vs_delegated_identity():
    """Passthrough evaluates the CALLER at the target; delegated evaluates the
    connection/identity.  The two modes must produce different effective ids."""
    r = run_fabric_case(f"{FIXTURES}/f03_passthrough_source_denied")
    chain = _chain(r)
    assert chain["shortcut"]["verdict"] == "allow"
    assert chain["shortcut_auth"]["verdict"] == "allow"
    assert chain["source_access"]["verdict"] == "deny"
    assert chain["source_access"]["identity"] == "spn-viewer"  # caller, not conn
    assert r["failure_layer"] == "source_access"


def test_delegated_connection_denied_at_target():
    r = run_fabric_case(f"{FIXTURES}/f04_delegated_ok")
    chain = _chain(r)
    assert chain["shortcut_auth"]["verdict"] == "allow"
    assert chain["source_access"]["verdict"] == "deny"
    # effective identity is the connection, never the caller
    assert chain["source_access"]["identity"] != "spn-viewer"


def test_confused_deputy_not_collapsed():
    """The caller being authorized on the shortcut lakehouse must NOT imply
    target authorization — f03 denies precisely because identities differ."""
    r = run_fabric_case(f"{FIXTURES}/f03_passthrough_source_denied")
    chain = _chain(r)
    assert chain["onelake_security"]["verdict"] == "allow"
    assert chain["source_access"]["verdict"] == "deny"


def test_missing_target_metadata_unresolved():
    r = run_fabric_case(f"{FIXTURES}/f05_shortcut_target_missing")
    assert r["status"] == "unresolved"
    ids = {f["rule_id"] for f in r["findings"]}
    assert "SF-FAB-001" in ids
    assert any(u["layer"] == "source_access" for u in r["unresolved"])
