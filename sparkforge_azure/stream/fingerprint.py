"""Streaming environment fingerprint (Cycle 4 memory reuse, prompt #160-163).

A memory record may only be reused when the environment matches: tenant /
namespace / workspace / hub / query identity axes, hashed canonically.
Checkpoint-location and schema-version axes are part of the fingerprint —
memory is never silently reused after a checkpoint or schema change.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def stream_fingerprint(case: Mapping[str, Any], facts: list[Any]) -> dict[str, Any]:
    """Deterministic environment fingerprint for a streaming case/report."""
    axes: dict[str, str] = {}
    for f in facts:
        if f.kind != "environment.scope":
            continue
        axes.setdefault(str(f.attrs.get("key")), str(f.attrs.get("value")))
    target = case.get("target") or {}
    for key, value in (("namespace_id", target.get("namespace_id")),
                       ("eventhub_id", target.get("eventhub_id")),
                       ("workspace_id", target.get("workspace_id")),
                       ("query_id", target.get("query_id"))):
        if value:
            axes.setdefault(key, str(value))
    for f in facts:
        if f.kind == "stream.checkpoint" and f.subject.get("location"):
            axes.setdefault("checkpoint_location",
                            str(f.subject["location"]))
        if f.kind == "schema.version" and f.subject.get("side") == "producer":
            axes.setdefault("schema_version",
                            str(f.subject.get("version")))
    return {"axes": axes,
            "axis_order": sorted(axes),
            "complete_axes": sorted(
                a for a in ("tenant_id", "namespace_id", "workspace_id")
                if a in axes)}


__all__ = ["stream_fingerprint"]
