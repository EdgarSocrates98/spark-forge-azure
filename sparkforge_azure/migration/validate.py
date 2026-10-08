"""Post-migration validation (SDD POST_MIGRATION_VALIDATION).

Dimensions are evaluated independently (prompt §147): row count alone is
never enough (§150); a performance regression never becomes a win (§154);
wrong target security identity fails (§156).  Results never auto-promote
(§163) — acceptance requires the evidence bundle.
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.migration.model import VALIDATION_DIMENSIONS

#: Regression beyond this ratio is a performance failure, not a "win".
PERF_REGRESSION_RATIO = 1.25


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _dim_verdict(f: Any) -> tuple[str, str]:
    """Evaluate one mig.validation fact -> (verdict, reason)."""
    dim = str(f.subject.get("dimension"))
    src, tgt = f.attrs.get("source_value"), f.attrs.get("target_value")
    ev = [f.id]
    if src is None or tgt is None:
        return "unknown", "evidencia ausente em um dos lados", ev
    if dim in {"functional", "data", "schema", "dq", "security",
               "lineage", "orchestration"}:
        ok = src == tgt
        if dim == "security" and not ok:
            return "fail", f"identidade/modelo diverge: {src}!={tgt}", ev
        return ("pass" if ok else "fail",
                "source == target" if ok else f"{src}!={tgt}", ev)
    if dim == "performance":
        try:
            s, t = float(src), float(tgt)
        except (TypeError, ValueError):
            return "unknown", "metrica nao numerica", ev
        if s <= 0:
            return "unknown", "baseline ausente", ev
        if t <= s:
            return "pass", f"target {t} <= source {s}", ev
        if t <= s * PERF_REGRESSION_RATIO:
            return "review", f"regression leve {t} vs {s}", ev
        return "fail", f"regression >{PERF_REGRESSION_RATIO}x: {t} vs {s}", ev
    if dim == "cost":
        return "unknown", "cost e estimado, nunca claim sem baseline", ev
    return "unknown", f"dimensao nao avaliavel: {dim}", ev


def validate_migration(facts: list[Any]) -> dict[str, Any]:
    """Multi-dimensional validation report (prompt §162)."""
    per_dim: dict[str, dict[str, Any]] = {}
    for f in _facts(facts, "mig.validation"):
        dim = str(f.subject.get("dimension"))
        verdict, reason, ev = _dim_verdict(f)
        cur = per_dim.setdefault(dim, {"dimension": dim, "verdict": "pass",
                                       "checks": []})
        cur["checks"].append({"asset": f.subject.get("asset_id"),
                              "metric": f.subject.get("metric"),
                              "verdict": verdict, "reason": reason,
                              "evidence": ev})
        order = {"fail": 0, "review": 1, "unknown": 2, "pass": 3}
        if order.get(verdict, 2) < order.get(cur["verdict"], 2):
            cur["verdict"] = verdict
    unknown_dims = [d for d in VALIDATION_DIMENSIONS if d not in per_dim]
    overall = "pass"
    if any(d["verdict"] == "fail" for d in per_dim.values()):
        overall = "fail"
    elif (any(d["verdict"] in {"review", "unknown"}
              for d in per_dim.values())
          or not per_dim or unknown_dims):
        overall = "review"
    return {
        "overall": overall,
        "dimensions": sorted(per_dim.values(),
                             key=lambda d: d["dimension"]),
        "unmeasured_dimensions": unknown_dims,
        "auto_promotion": False,
        "note": "aceitacao exige evidence bundle; resultado nunca "
                "auto-promove (prompt §163)",
    }


__all__ = ["PERF_REGRESSION_RATIO", "validate_migration"]
