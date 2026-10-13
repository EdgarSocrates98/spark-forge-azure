"""Deterministic compatibility engine (SDD MIGRATION_COMPATIBILITY).

Every dimension produces a status from the closed vocabulary
(``COMPAT_STATUS``) with evidence.  There is no magic migration score: a
score, when present, is an auxiliary aggregation that never hides
blockers/unknowns/manual refactors.  Official Microsoft assessment results
are DATA_ONLY evidence — divergence is REVIEW + conflict, never a silent
override (prompt §34/§228).
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.migration.model import OFFICIAL_TO_INTERNAL, READINESS


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def map_official(status: object) -> str:
    """Official label -> internal readiness (provenance kept by caller)."""
    return OFFICIAL_TO_INTERNAL.get(str(status or "").strip().lower(),
                                    "UNRESOLVED")


def assess_readiness(facts: list[Any],
                     dim_results: list[dict[str, Any]],
                     asset_key: str | None = None) -> dict[str, Any]:
    """Combine dimension verdicts (+ optional official assessment) into a
    readiness state.  Worst-of ordering: BLOCKED > MANUAL > REVIEW >
    DEFERRED > UNRESOLVED > READY.

    The official result is evidence: Forge's deterministic result stands,
    and divergence is reported as ``conflict`` -> REVIEW.
    """
    internal = _internal_from_dims(dim_results)
    official_rows = _facts(facts, "mig.assessment_result")
    conflicts: list[dict[str, Any]] = []
    official_internal = None
    if official_rows:
        row = official_rows[0]
        if asset_key is not None:
            row = next((r for r in official_rows
                        if str(r.subject.get("asset_id")) == asset_key), row)
        official_internal = map_official(row.attrs.get("official_status"))
        if official_internal != internal and not (
                official_internal == "READY" and internal == "UNRESOLVED"):
            conflicts.append({
                "asset": asset_key or str(row.subject.get("asset_id")),
                "official": row.attrs.get("official_status"),
                "official_internal": official_internal,
                "forge_internal": internal,
                "source": row.provenance.get("source")})
    if conflicts:
        internal = "REVIEW"
    stale = _assessment_stale(official_rows)
    return {
        "readiness": internal,
        "official_status": (official_rows[0].attrs.get("official_status")
                            if official_rows else None),
        "official_internal": official_internal,
        "official_assessment": ("unavailable" if not official_rows
                                else "present"),
        "assessment_stale": stale,
        "conflicts": conflicts,
        "dimensions": dim_results,
    }


def _assessment_stale(rows: list[Any], max_age_days: int = 90) -> bool:
    """Assessment freshness (prompt §35/§208): old exports are flagged."""
    import datetime as _dt
    for r in rows:
        at = r.attrs.get("assessed_at")
        if not at:
            continue
        try:
            ts = _dt.datetime.fromisoformat(
                str(at).replace("Z", "+00:00"))
            if (_dt.datetime.now(_dt.timezone.utc) - ts).days > max_age_days:
                return True
        except ValueError:
            continue
    return False


def _internal_from_dims(dims: list[dict[str, Any]]) -> str:
    """Worst-of aggregation; 'unknown' dimension keeps UNRESOLVED floor."""
    statuses = {str(d.get("status", "unknown")) for d in dims}
    if "unsupported" in statuses:
        return "BLOCKED"
    if "manual_refactor" in statuses:
        return "MANUAL"
    if not dims:
        return "UNRESOLVED"
    if "unknown" in statuses:
        return "REVIEW" if statuses - {"unknown", "compatible",
                                      "compatible_with_change"} \
            else "UNRESOLVED"
    if "preview" in statuses or "compatible_with_change" in statuses:
        return "REVIEW"
    return "READY"


def compat_score(dim_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Auxiliary aggregation — never hides blockers/unknowns (§39-40)."""
    counts: dict[str, int] = {}
    for d in dim_results:
        counts[str(d.get("status", "unknown"))] = (
            counts.get(str(d.get("status", "unknown")), 0) + 1)
    total = len(dim_results) or 1
    return {
        "compatible_pct": round(
            100 * counts.get("compatible", 0) / total, 1),
        "blockers": counts.get("unsupported", 0),
        "unknowns": counts.get("unknown", 0),
        "manual_refactors": counts.get("manual_refactor", 0),
        "preview": counts.get("preview", 0),
        "dimension_count": len(dim_results),
    }


def readiness_rank(state: str) -> int:
    return READINESS.index(state) if state in READINESS else 0


__all__ = [
    "assess_readiness", "compat_score", "map_official", "readiness_rank",
]
