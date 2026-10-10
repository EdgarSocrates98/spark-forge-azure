"""Spark Forge Azure → ForgeGraphView/v1 adapter.

Projects the real Graphfy graph (``graph build`` output, layered nodes
with static/live/artifact/knowledge provenance) onto the view contract.
Provenance.kind maps explicitly: live/artifact → observed, static/
knowledge → declared; the raw kind is preserved verbatim in
``EdgeView.provenance``/node attributes.
"""

from __future__ import annotations

from pathlib import Path

from sparkforge_azure._graphview import (
    ForgeGraphView,
    GraphEdgeView,
    GraphNodeView,
    new_descriptor,
)

PROVIDER = "spark-forge-azure"

# azure Provenance.kind → view epistemic (raw value kept in provenance)
_PROV_EPISTEMIC = {
    "live": "observed",
    "artifact": "observed",
    "static": "declared",
    "knowledge": "declared",
}


def _epistemic(prov_kind: str) -> str:
    return _PROV_EPISTEMIC.get(prov_kind, "unknown")


def build_view(graph_path: str | Path) -> ForgeGraphView | None:
    """A saved ``graph build`` JSON → view. None when unreadable."""
    from sparkforge_azure.graph.store import load_graph

    try:
        g = load_graph(graph_path)
    except Exception:
        return None
    desc = new_descriptor(
        provider_id=PROVIDER,
        domain="azure-data",
        graph_id="azure-graph",
        capabilities=(
            "node_inspect",
            "edge_inspect",
            "neighbors",
            "paths",
            "impact_analysis",
            "search",
            "filter",
            "export",
        ),
    )
    object.__setattr__(desc, "node_count", len(g.nodes))
    object.__setattr__(desc, "edge_count", len(g.edges))
    object.__setattr__(
        desc, "available_layers", tuple(sorted({n.layer for n in g.nodes.values()}))
    )
    nodes = tuple(
        GraphNodeView(
            id=n.id,
            kind=n.kind,
            label=n.attrs.get("label", n.id) if hasattr(n, "attrs") else n.id,
            domain=n.layer,
            source_provider=PROVIDER,
            attributes=dict(n.attrs),
            epistemic_state=_epistemic(n.provenance.kind),
            evidence_refs=(f"{n.provenance.kind}:{n.provenance.source}",),
        )
        for n in g.nodes.values()
    )
    edges = tuple(
        GraphEdgeView(
            id="|".join(e.key),
            source=e.source,
            target=e.target,
            kind=e.relation,
            provenance=e.provenance.kind,
            epistemic_state=_epistemic(e.provenance.kind),
            evidence_refs=(f"{e.provenance.kind}:{e.provenance.source}",),
            attributes=dict(e.attrs),
        )
        for e in g.edges.values()
    )
    return ForgeGraphView(descriptor=desc, nodes=nodes, edges=edges)
