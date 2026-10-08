"""Migration environment fingerprint (Cycle 5 memory reuse, prompt §206-208).

A migration memory record may only be reused when the environment matches:
tenant / subscription / factory / workspace / spark versions / assessment
version+date — Fabric parity changes quickly, so assessment staleness is
part of the fingerprint itself.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def migration_fingerprint(case: Mapping[str, Any],
                          facts: list[Any]) -> dict[str, Any]:
    axes: dict[str, str] = {}
    for f in facts:
        if f.kind != "environment.scope":
            continue
        axes.setdefault(str(f.attrs.get("key")), str(f.attrs.get("value")))
    target = case.get("target") or {}
    for key, value in (("factory_id", target.get("factory_id")),
                       ("synapse_workspace_id",
                        target.get("synapse_workspace_id")),
                       ("fabric_workspace_id",
                        target.get("fabric_workspace_id"))):
        if value:
            axes.setdefault(key, str(value))
    for f in facts:
        if f.kind == "mig.spark_pool" and f.attrs.get("spark_version"):
            axes.setdefault("spark_version",
                            str(f.attrs["spark_version"]))
        if f.kind == "mig.assessment_result":
            axes.setdefault("assessment_tool",
                            str(f.attrs.get("tool")))
            axes.setdefault("assessed_at",
                            str(f.attrs.get("assessed_at")))
    return {"axes": axes,
            "axis_order": sorted(axes),
            "complete_axes": sorted(
                a for a in ("tenant_id", "subscription_id",
                            "fabric_workspace_id")
                if a in axes)}


__all__ = ["migration_fingerprint"]
