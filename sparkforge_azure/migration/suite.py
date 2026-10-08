"""Migration lab suite runner: run every case bundle and check the
``expect:`` block (status / plan.status / readiness of a named asset).

Executable form of the Forge Lab migration scenarios: fixtures under
``tests/fixtures/migration/`` are the cases; ``expect.*`` is the oracle.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sparkforge_azure.migration import casefile, pipeline


def _checks(case: dict[str, Any], report: dict[str, Any]) -> dict[str, bool]:
    exp = case.get("expect") or {}
    checks: dict[str, bool] = {}
    if exp.get("status") is not None:
        checks["status"] = report["status"] == exp["status"]
    if exp.get("plan_status") is not None:
        checks["plan_status"] = (
            report["plan"]["status"] == exp["plan_status"])
    for key, want in (exp.get("readiness") or {}).items():
        checks[f"readiness:{key}"] = (
            report["readiness"].get(key) == want)
    if exp.get("verdict") is not None and report.get("validation"):
        checks["validation"] = (
            report["validation"]["overall"] == exp["verdict"])
    if exp.get("strategy") is not None:
        checks["strategy"] = any(
            r.get("strategy") == exp["strategy"]
            for r in report["recommendations"])
    if exp.get("sharing_finding") is not None:
        checks["sharing"] = any(
            f.get("kind") == exp["sharing_finding"]
            for f in report["connection_sharing"])
    if exp.get("upstream_blocker") is not None:
        checks["upstream_blocker"] = bool(report["upstream_blockers"])
    return checks


def run_migration_suite(root: str | Path,
                        *, profile: str = "balanced") -> dict[str, Any]:
    """Run ``run_migration_case`` on every sub-directory with a
    ``case.yaml``."""
    base = Path(root)
    if not base.is_dir():
        raise casefile.MigrationCaseError(
            f"suite directory not found: {base}")
    bundles = sorted(
        p.parent for p in base.iterdir()
        if p.is_dir() for p in [p / "case.yaml"] if p.is_file())
    if not bundles:
        raise casefile.MigrationCaseError(
            f"no case.yaml bundles under {base}")
    cases: list[dict[str, Any]] = []
    for b in bundles:
        bundle = casefile.load_bundle(b)
        report = pipeline.run_migration_case(b, profile=profile)
        checks = _checks(bundle.case, report)
        cases.append({
            "case": b.name,
            "expected": bundle.case.get("expect") or {},
            "actual": {"status": report["status"],
                       "plan_status": report["plan"]["status"],
                       "readiness": report["readiness"]},
            "verdict": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "conflicts": report["conflicts"],
            "unresolved": report["unresolved"],
            "trust_taint": report["trust"]["taint"],
        })
    failed = [c["case"] for c in cases if c["verdict"] == "fail"]
    return {
        "status": "pass" if not failed else "fail",
        "suite_root": base.as_posix(),
        "passed": len(cases) - len(failed),
        "failed": len(failed),
        "cases": cases,
        "authority": "data_only",
    }


__all__ = ["run_migration_suite"]
