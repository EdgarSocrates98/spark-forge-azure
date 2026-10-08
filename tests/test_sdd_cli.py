"""Contrato do `sparkforge-azure sdd check|status`: um JSON, exit 0/1.

O verbo é a superfície documentada do gate SDD (AGENTS.md/CONTRIBUTING.md)
— antes ele só existia como API (`sdd.checks.check`)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", *argv],
        capture_output=True, text=True, cwd=ROOT)


def test_sdd_check_all_features_ok() -> None:
    r = _run("sdd", "check")
    doc = json.loads(r.stdout)
    assert "MIGRATION_INVENTORY" in doc["features"]
    if r.returncode != 0:
        # Mid-cycle SDDs may refuse with `test_not_written` — the planning
        # red the gate exists to show. Any OTHER refusal code is a defect.
        codes = {ref.get("code") for ref in doc.get("unresolved", [])}
        assert codes and codes <= {"test_not_written"}, doc


def test_sdd_check_feature_scope() -> None:
    r = _run("sdd", "check", "--feature", "MIGRATION_INVENTORY")
    doc = json.loads(r.stdout)
    assert r.returncode == 0, doc
    assert doc["features"] == ["MIGRATION_INVENTORY"]


def test_sdd_check_refusal_exits_1(tmp_path: Path) -> None:
    """A broken artifact chain refuses — named, never silent."""
    sdd = tmp_path / "docs" / "sdd" / "BROKEN_FEATURE"
    sdd.mkdir(parents=True)
    (sdd / "define.md").write_text(
        "---\nid: BROKEN_FEATURE\ntitle: x\n---\n", encoding="utf-8")
    from sparkforge_azure.sdd.checks import check
    out = check(tmp_path)
    assert not out["ok"]
    assert out["refused"], "broken feature must refuse with named reasons"


def test_sdd_status_lists_features() -> None:
    r = _run("sdd", "status")
    doc = json.loads(r.stdout)
    assert r.returncode == 0, doc
    names = {f["feature"] for f in doc["features"]}
    assert "MIGRATION_INVENTORY" in names
    assert all(f["phase"] for f in doc["features"])
