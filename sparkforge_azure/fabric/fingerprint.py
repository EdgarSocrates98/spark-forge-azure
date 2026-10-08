"""Fabric environment fingerprint (prompt #367-370).

A memory record or report may only be reused across environments when the
environment matches.  For Fabric the identity axes are tenant / capacity /
workspace / item / runtime / lakehouse — taken from ``environment.scope``
facts plus the case target, hashed canonically.  Missing axes are simply
absent from the fingerprint (never invented).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def fabric_fingerprint(case: Mapping[str, Any], facts: list[Any]) -> dict[str, Any]:
    """Deterministic environment fingerprint for a Fabric case/report."""
    axes: dict[str, str] = {}
    for f in facts:
        if f.kind != "environment.scope":
            continue
        key = str(f.attrs.get("key"))
        val = str(f.attrs.get("value"))
        # First writer wins per axis — a real conflict is surfaced separately
        # by SF-FAB-013, never silently resolved here.
        axes.setdefault(key, val)
    target = case.get("target") or {}
    for key, value in (("workspace_id", target.get("workspace_id")),
                       ("lakehouse_id", target.get("lakehouse_id")),
                       ("item_id", target.get("item_id"))):
        if value:
            axes.setdefault(key, str(value))
    env_versions = sorted(
        str(f.attrs["runtime_version"])
        for f in facts
        if f.kind == "fabric.environment" and f.attrs.get("runtime_version"))
    if env_versions:
        axes.setdefault("fabric_runtime", env_versions[0])
    return {"axes": axes,
            "axis_order": sorted(axes),
            "complete_axes": sorted(
                a for a in ("tenant_id", "capacity_id", "workspace_id")
                if a in axes)}


__all__ = ["fabric_fingerprint"]
