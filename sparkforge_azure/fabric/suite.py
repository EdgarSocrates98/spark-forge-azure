"""Fabric lab suite runner: run every case bundle in a directory and check
each report against the ``expect:`` block declared in its ``case.yaml``.

Executable form of the Fabric Lab scenarios (prompt #126-136 for Cycle 3):
the fixtures under ``tests/fixtures/fabric/`` are the cases,
``expect.status`` / ``expect.failure_layer`` are the oracle.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sparkforge_azure.fabric import casefile, pipeline


def _expected(case: dict[str, Any]) -> dict[str, Any]:
    exp = case.get("expect") or {}
    return {"status": exp.get("status"), "failure_layer": exp.get("failure_layer")}


def run_fabric_suite(root: str | Path, *, profile: str = "balanced") -> dict[str, Any]:
    """Run ``run_fabric_case`` on every sub-directory with a ``case.yaml``."""
    base = Path(root)
    if not base.is_dir():
        raise casefile.CaseError(f"suite directory not found: {base}")
    bundles = sorted(
        p.parent for p in base.iterdir()
        if p.is_dir() for p in [p / "case.yaml"] if p.is_file())
    if not bundles:
        raise casefile.CaseError(f"no case.yaml bundles under {base}")
    cases: list[dict[str, Any]] = []
    for b in bundles:
        bundle = casefile.load_bundle(b)
        report = pipeline.run_fabric_case(b, profile=profile)
        exp = _expected(bundle.case)
        checks = {
            "status": exp["status"] is None or report["status"] == exp["status"],
            "failure_layer": (exp["failure_layer"] is None
                              or report["failure_layer"] == exp["failure_layer"]),
        }
        cases.append({
            "case": b.name,
            "expected": exp,
            "actual": {"status": report["status"],
                       "failure_layer": report["failure_layer"]},
            "verdict": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "evidence_paths": report.get("evidence_paths", {}),
            "trust_taint": report["trust"]["taint"],
            "unresolved": report["unresolved"],
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


__all__ = ["run_fabric_suite"]
