"""Access lab: ``diagnose --suite`` runs all case bundles against expect:."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sparkforge_azure.azure import suite
from sparkforge_azure.azure.casefile import CaseError

FIXTURES = Path(__file__).parent / "fixtures" / "access"


def test_suite_all_ten_scenarios_pass() -> None:
    report = suite.run_suite(FIXTURES)
    assert report["status"] == "pass"
    assert report["passed"] == 10
    assert report["failed"] == 0
    by_case = {c["case"]: c for c in report["cases"]}
    # prompt scenarios 1-10 mapeados 1:1
    assert by_case["s01_uc_privilege_denied"]["actual"]["failure_layer"] == "unity_catalog"
    assert by_case["s02_rbac_control_plane_only"]["actual"]["failure_layer"] == "azure_rbac"
    assert by_case["s03_acl_missing_execute"]["actual"]["failure_layer"] == "adls_acl"
    assert by_case["s04_private_dns_not_linked"]["actual"]["failure_layer"] == "network"
    assert by_case["s05_workspace_not_bound"]["actual"]["failure_layer"] == "workspace_binding"
    assert by_case["s06_no_covering_location"]["actual"]["failure_layer"] == "external_location"
    assert by_case["s07_governance_bypass"]["actual"]["failure_layer"] == "governance_bypass"
    assert by_case["s08_legacy_access_mode"]["actual"]["failure_layer"] == "runtime"
    assert by_case["s09_delta_direct_path"]["actual"]["failure_layer"] == "delta_perf"
    assert by_case["s10_missing_evidence"]["actual"]["failure_layer"] == "unresolved"


def test_suite_surfaces_evidence_path_per_case() -> None:
    """Cada Lab scenario precisa expected evidence path (prompt #2491)."""
    report = suite.run_suite(FIXTURES)
    for case in report["cases"]:
        assert "evidence_paths" in case


def test_suite_fails_on_wrong_expectation(tmp_path: Path) -> None:
    import shutil

    case = tmp_path / "bad"
    shutil.copytree(FIXTURES / "s01_uc_privilege_denied", case)
    case_yaml = (case / "case.yaml").read_text(encoding="utf-8")
    (case / "case.yaml").write_text(
        case_yaml.replace("failure_layer: unity_catalog", "failure_layer: network"),
        encoding="utf-8")
    report = suite.run_suite(tmp_path)
    assert report["status"] == "fail"
    assert report["cases"][0]["checks"]["failure_layer"] is False


def test_suite_empty_dir_refused(tmp_path: Path) -> None:
    with pytest.raises(CaseError):
        suite.run_suite(tmp_path)


def test_suite_via_cli(tmp_path: Path) -> None:
    import subprocess
    import sys

    # cwd isolado: o diagnose grava spans no `.sparkforge-azure/traces.db`
    # do cwd -- rodar na raiz do repo criaria artefato de estado de teste.
    proc = subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main",
         "diagnose", "--suite", str(FIXTURES)],
        capture_output=True, text=True, cwd=tmp_path)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "pass"
    assert payload["passed"] == 10
