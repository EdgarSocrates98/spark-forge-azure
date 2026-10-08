"""SDD FABRIC_CORE — end-to-end offline pipeline contract."""
from __future__ import annotations

import pytest

from sparkforge_azure.fabric.casefile import CaseError, load_bundle
from sparkforge_azure.fabric.pipeline import PUBLIC_LAYERS, run_fabric_case
from sparkforge_azure.fabric.suite import run_fabric_suite

FIXTURES = "tests/fixtures/fabric"


def test_pipeline_end_to_end_offline():
    r = run_fabric_case(f"{FIXTURES}/f14_malicious_metadata")
    for key in ("status", "failure_layer", "diagnosis", "findings",
                "unresolved", "facts", "fabric_graph", "evidence_paths",
                "knowledge", "overhead", "context_quality", "trust",
                "receipt"):
        assert key in r, key
    assert "graph" in r["overhead"] and "stages" in r["overhead"]
    for stage in ("load_case", "extract", "notebook_scan", "diagnose",
                  "rules", "graph", "evidence_trust"):
        assert stage in r["overhead"]["stages"], stage


def test_suite_all_cases():
    r = run_fabric_suite(FIXTURES)
    assert r["failed"] == 0, [c["case"] for c in r["cases"]
                             if c["verdict"] == "fail"]
    assert r["authority"] == "data_only"


def test_unknown_never_assumed():
    r = run_fabric_case(f"{FIXTURES}/f15_insufficient")
    assert r["status"] == "unresolved"
    assert r["failure_layer"] == "unresolved"
    assert any(u.get("artifact") for u in r["unresolved"])
    # every unresolved names the artifact that would close it
    for u in r["unresolved"]:
        assert "artifact_present" in u or u["layer"] not in {
            "fabric_workspace", "item_permission", "onelake_security",
            "capacity"}


def test_public_layers_cover_chain():
    chain_layers = {"fabric_workspace", "item_permission", "onelake_security",
                    "shortcut", "shortcut_auth", "source_access", "lakehouse",
                    "spark_runtime", "spark_job", "capacity", "data_factory"}
    assert chain_layers <= set(PUBLIC_LAYERS)


def test_bundle_missing_case_rejected(tmp_path):
    with pytest.raises(CaseError):
        load_bundle(tmp_path)


def test_evidence_paths_have_facts():
    r = run_fabric_case(f"{FIXTURES}/f02_onelake_denied")
    for rule_id, path in r["evidence_paths"].items():
        assert path["facts"], rule_id
