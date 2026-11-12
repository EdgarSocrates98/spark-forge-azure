"""Federated SDD adapter tests — Onda 5C (sparkforge_azure)."""

from __future__ import annotations

import json

from sparkforge_azure.sdd import federated


def test_phase_map_identity_for_shared_names():
    for phase in ("explore", "define", "design", "plan", "build_report",
                  "ship"):
        assert federated.map_phase(phase) == phase


def test_gate_from_evaluate_shape():
    native = {
        "ok": False,
        "refused": [{"code": "upstream_hash_stale", "feature": "F1",
                     "path": "design.md", "field": "upstream.sha256",
                     "unlock": "sparkforge-azure sdd stamp"}],
        "unresolved": [{"code": "criterion_unverified", "feature": "F1",
                        "path": "define.md",
                        "unlock": "run the criterion"}],
    }
    gate = federated.to_gate("F1", "design", native)
    assert gate["schema"] == "forge/SDDGate/v1"
    assert gate["refused"][0]["path"] == "design.md"
    assert gate["unresolved"][0]["code"] == "criterion_unverified"


def test_evidence_computes_sha(tmp_path):
    f = tmp_path / "e.txt"
    f.write_text("x")
    ev = federated.to_evidence(f, kind="gate", agent="t",
                               command=["sdd", "check"])
    assert ev["sha256"].startswith("sha256:")


def test_federated_view_reads_receipts(tmp_path):
    (tmp_path / "receipts").mkdir()
    (tmp_path / "receipts" / "r1.json").write_text(json.dumps({
        "schema": "forge/SDDReceipt/v1", "feature": "F1", "phase": "ship",
        "action": "release", "actor": "a",
        "recorded_at": "2026-04-05T10:00:00Z"}))
    view = federated.federated_view(tmp_path, feature="F1")
    assert len(view["forge/SDDReceipt/v1"]) == 1
