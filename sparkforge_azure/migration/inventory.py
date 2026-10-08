"""Estate discovery & summary (SDD MIGRATION_INVENTORY).

Pure aggregation over extracted facts: asset counts, dependency counts and
the readiness census.  Absence of assessment evidence is UNRESOLVED, never
READY (prompt §29).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def estate_summary(facts: list[Any],
                   readiness: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Asset/dependency counts + readiness census (prompt §28)."""
    asset_kinds = {f.kind for f in facts if f.kind.startswith("mig.")
                   and f.kind not in {"mig.assessment_result",
                                      "mig.validation"}}
    assets = [f for f in facts if f.kind in asset_kinds]
    deps = _facts(facts, "dep.edge")
    per_asset = dict(readiness or {})
    census = {"ready": 0, "review": 0, "blocked": 0, "manual": 0,
              "deferred": 0, "unresolved": 0}
    for f in assets:
        key = next(iter(f.subject.values()))
        st = str(per_asset.get(key, "UNRESOLVED")).upper()
        bucket = {"READY": "ready", "REVIEW": "review", "BLOCKED": "blocked",
                  "MANUAL": "manual", "DEFERRED": "deferred"}.get(
                      st, "unresolved")
        census[bucket] += 1
    return {
        "asset_count": len(assets),
        "asset_kinds": sorted(asset_kinds),
        "dependency_count": len(deps),
        "unsupported_count": census["blocked"],
        "needs_review": census["review"],
        "ready": census["ready"],
        "manual": census["manual"],
        "deferred": census["deferred"],
        "unknown": census["unresolved"],
        "assessment_present": bool(_facts(facts, "mig.assessment_result")),
    }


def dependency_map(facts: list[Any]) -> dict[str, list[dict[str, str]]]:
    """src -> [{relation, dst}] adjacency for planner/graph reuse."""
    out: dict[str, list[dict[str, str]]] = {}
    for e in _facts(facts, "dep.edge"):
        out.setdefault(str(e.subject["src"]), []).append(
            {"relation": str(e.subject["relation"]),
             "dst": str(e.subject["dst"])})
    return {k: sorted(v, key=lambda d: (d["relation"], d["dst"]))
            for k, v in sorted(out.items())}


__all__ = ["dependency_map", "estate_summary"]
