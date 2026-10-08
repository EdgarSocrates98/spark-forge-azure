"""Fabric-specific waste detectors (prompt #365-366).

Operates on AgentOps span names/results — the same ledger spans the
pipeline emits (``fabric.*``) and the collector emits (``fetch``-style
names in resultado).  Every detection is labeled ``hypothesis`` — pattern
evidence, never an observed cloud cost.

Detectors:
* ``repeated_workspace_fetch``   — the same workspace/artifact fetched >1
* ``repeated_item_fetch``        — repeated item-detail fetches
* ``repeated_shortcut_lookup``   — shortcut list/get called repeatedly
* ``whole_workspace_after_graph``— a full items list fetched after a
  graph-assisted answer already identified the item
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: span-name fragment -> waste kind
_FETCH_KINDS = {
    "workspace": "repeated_workspace_fetch",
    "items": "repeated_item_fetch",
    "item": "repeated_item_fetch",
    "shortcut": "repeated_shortcut_lookup",
}


def _kind_of(name: str) -> str | None:
    for frag, kind in _FETCH_KINDS.items():
        if frag in name:
            return kind
    return None


def detect_fabric_waste(spans: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Each finding is a hypothesis dict — a candidate inefficiency to
    investigate, never a measured cost."""
    hits: dict[str, int] = {}
    graph_assisted = False
    for s in spans:
        name = str(s.get("name", ""))
        res = s.get("resultado") or {}
        if isinstance(res, Mapping) and res.get("graph_assisted"):
            graph_assisted = True
        kind = _kind_of(name)
        if kind:
            hits[name] = hits.get(name, 0) + 1
    findings: list[dict[str, Any]] = []
    for name, count in sorted(hits.items()):
        if count > 1:
            findings.append({
                "kind": _kind_of(name), "evidence": "hypothesis",
                "detail": f"{name} chamado {count}x no mesmo run",
                "span": name, "count": count})
    if graph_assisted and any("list" in n and "items" in n
                              for n in hits):
        findings.append({
            "kind": "whole_workspace_after_graph", "evidence": "hypothesis",
            "detail": "list-items full fetch observed after a graph-assisted "
                      "hit — candidate to narrow the query scope"})
    return findings


__all__ = ["detect_fabric_waste"]
