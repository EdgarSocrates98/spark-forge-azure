"""Counterfactual context eval (prompt #112).

For each artifact file in a case bundle, remove it, re-run the diagnosis in
a temp copy and report whether ``status``/``failure_layer`` changed.  This
measures *evidence sensitivity*: which artifacts the decision actually
depends on.  Eval-only — it never feeds a verdict.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from sparkforge_azure.azure import casefile, pipeline


def counterfactual_sweep(bundle_root: str | Path,
                         *, profile: str = "balanced") -> dict[str, Any]:
    """Drop each artifact file once and re-diagnose; report the deltas."""
    root = Path(bundle_root)
    bundle = casefile.load_bundle(root)
    base = pipeline.run_case(root, profile=profile)
    baseline = {"status": base["status"], "failure_layer": base["failure_layer"]}
    # All candidate inputs: declared artifacts + every notebook file scanned.
    candidates: list[Path] = []
    for name in casefile.ARTIFACT_NAMES + ("case",):
        src = bundle.sources.get(name)
        if src:
            p = root / src
            if p.is_file():
                candidates.append(p)
    candidates.extend(bundle.notebook_files)
    rows: list[dict[str, Any]] = []
    for victim in sorted(candidates):
        rel = victim.relative_to(root).as_posix()
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "bundle"
            shutil.copytree(root, copy)
            (copy / rel).unlink()
            try:
                report = pipeline.run_case(copy, profile=profile)
                outcome = {"status": report["status"],
                           "failure_layer": report["failure_layer"]}
                changed = outcome != baseline
                row = {"removed": rel, "changed": changed, "outcome": outcome}
                if changed:
                    row["baseline"] = baseline
            except casefile.CaseError as exc:
                row = {"removed": rel, "changed": True, "outcome": "error",
                       "error": str(exc), "baseline": baseline}
        rows.append(row)
    changed = [r for r in rows if r["changed"]]
    return {
        "case": str(bundle.case.get("name", root.name)),
        "baseline": baseline,
        "removed_items": len(rows),
        "verdict_changed": len(changed),
        "sensitivity": round(len(changed) / len(rows), 4) if rows else None,
        "rows": rows,
        "authority": "data_only",
    }


__all__ = ["counterfactual_sweep"]
