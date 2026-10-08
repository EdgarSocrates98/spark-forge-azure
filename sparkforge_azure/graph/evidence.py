"""Evidence paths over the access graph (P0-C, AC4).

A finding is only as good as the evidence chain behind it.  The diagnosis
pipeline anchors finding nodes with ``evidenced_by`` edges to fact nodes whose
provenance names the bundle artifact that produced them.  This module walks
that chain so consumers get ``finding -> facts -> source artifacts`` straight
from the graph instead of a parallel bookkeeping structure.
"""
from __future__ import annotations

from typing import Any

from sparkforge_azure.graph.model import Graph


def evidence_path(graph: Graph, finding_node: str) -> dict[str, Any]:
    """finding node -> fact node ids -> artifact sources (deterministic)."""
    node = graph.nodes.get(finding_node)
    if node is None or node.kind != "finding":
        raise ValueError(f"not a finding node: {finding_node!r}")
    fact_ids = sorted(e.target for e in graph.out_edges(finding_node)
                      if e.relation == "evidenced_by")
    artifacts: set[str] = set()
    observed_at: set[str] = set()
    for fid in fact_ids:
        fact_node = graph.nodes.get(fid)
        if fact_node is None:
            continue
        artifacts.add(fact_node.provenance.source)
        if fact_node.provenance.observed_at:
            observed_at.add(fact_node.provenance.observed_at)
    return {
        "finding": finding_node,
        "facts": fact_ids,
        "artifacts": sorted(artifacts),
        "observed_at": sorted(observed_at),
        # full walk, oldest hop first rendered left-to-right
        "path": [finding_node, *fact_ids, *sorted(artifacts)],
    }


def evidence_paths(graph: Graph) -> dict[str, Any]:
    """All evidence-layer finding nodes -> their evidence path."""
    return {
        nid: evidence_path(graph, nid)
        for nid in sorted(graph.nodes)
        if graph.nodes[nid].layer == "evidence"
        and graph.nodes[nid].kind == "finding"
    }


__all__ = ["evidence_path", "evidence_paths"]
