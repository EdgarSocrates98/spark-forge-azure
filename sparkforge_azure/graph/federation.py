"""Federated Graphfy (section 67): static code graph + Azure observed graph +
artifact graph + knowledge graph.

Composition rule (section 64), enforced here and nowhere relaxed:

* nodes unify ONLY when their ids are identical (ARM id, Databricks workspace
  id, Fabric GUID, repository path, knowledge id);
* cross-graph edges come ONLY from declared bindings or verified references
  (an explicit id carried as an attribute, e.g. ``databricks_workspace_id``);
* similar or identical display names NEVER link anything.  Name collisions
  are reported (``ambiguous_names``) and unbound candidates land in
  ``unresolved`` with a reason.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from sparkforge_azure.graph.arm import is_arm_id
from sparkforge_azure.graph.model import Edge, Graph, Provenance, azure_node_id

_FED = Provenance("static", "graphfy.federation")


@dataclass
class FederationResult:
    graph: Graph
    ambiguous_names: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    @property
    def unresolved(self) -> list[dict[str, Any]]:
        return self.graph.unresolved

    def to_dict(self) -> dict[str, Any]:
        out = self.graph.to_dict()
        out["ambiguous_names"] = self.ambiguous_names
        out["sources"] = self.sources
        return out


def federate(
    static: Graph | None = None,
    live: Graph | None = None,
    artifact: Graph | None = None,
    knowledge: Graph | None = None,
    *,
    bindings: Iterable[Mapping[str, str]] = (),
) -> FederationResult:
    parts = [("static", static), ("live", live), ("artifact", artifact),
             ("knowledge", knowledge)]
    graph = Graph()
    sources: list[str] = []
    for label, part in parts:
        if part is None:
            continue
        sources.append(label)
        graph = graph.merge(part)
    _explicit_bindings(graph, bindings)
    _alias_ids(graph)
    _drop_dangling(graph)
    if live is not None:
        _declared_vs_observed(graph, live)
    _unbound_iac(graph)
    ambiguous = _ambiguous_names(graph)
    graph.meta = {"kind": "federated", "sources": sources}
    return FederationResult(graph, ambiguous, sources)


def _explicit_bindings(graph: Graph, bindings: Iterable[Mapping[str, str]]) -> None:
    for b in bindings:
        source = str(b.get("source", ""))
        target = str(b.get("target", ""))
        if is_arm_id(target):
            target = azure_node_id(target)
        if source not in graph.nodes or target not in graph.nodes:
            graph.add_unresolved({
                "reason": "binding_endpoint_missing", "source": source, "target": target,
                "missing": sorted(x for x in (source, target) if x not in graph.nodes),
            })
            continue
        graph.add_edge(Edge(source, "binds_to", target, {"declared": True}, _FED))


def _alias_ids(graph: Graph) -> None:
    """Link alternate explicit ids of the SAME resource (verified reference)."""

    for nid in sorted(graph.nodes):
        node = graph.nodes[nid]
        if node.layer != "azure":
            continue
        dbx = node.attrs.get("databricks_workspace_id")
        if dbx:
            alias = f"azure:databricks:{dbx}"
            if alias != nid and alias in graph.nodes:
                graph.add_edge(Edge(nid, "same_as", alias,
                                    {"via": "databricks_workspace_id"}, _FED))
        fab = node.attrs.get("fabric_workspace_id")
        if fab:
            alias = f"azure:fabric:{str(fab).lower()}"
            if alias != nid and alias in graph.nodes:
                graph.add_edge(Edge(nid, "same_as", alias, {"via": "fabric_workspace_id"}, _FED))


def _drop_dangling(graph: Graph) -> None:
    for edge in graph.dangling_edges():
        missing = sorted(x for x in (edge.source, edge.target) if x not in graph.nodes)
        graph.add_unresolved({"reason": "dangling_reference", "source": edge.source,
                              "relation": edge.relation, "target": edge.target,
                              "missing": missing})
        del graph.edges[edge.key]


def _declared_vs_observed(graph: Graph, live: Graph) -> None:
    for nid in sorted(graph.nodes):
        node = graph.nodes[nid]
        if node.layer == "azure" and node.attrs.get("declared") and nid not in live.nodes:
            graph.add_unresolved({"reason": "declared_not_observed", "id": nid,
                                  "declared_name": node.attrs.get("declared_name")})


def _unbound_iac(graph: Graph) -> None:
    bound = {k[0] for k in graph.edges if k[1] == "binds_to"}
    by_name: dict[str, list[str]] = {}
    for nid, node in graph.nodes.items():
        if node.layer == "azure" and isinstance(node.attrs.get("name"), str):
            by_name.setdefault(node.attrs["name"].lower(), []).append(nid)
    for nid in sorted(graph.nodes):
        node = graph.nodes[nid]
        rtype = str(node.attrs.get("resource_type", ""))
        if node.kind != "symbol" or node.attrs.get("iac") != "terraform":
            continue
        if not rtype.startswith("azurerm_") or nid in bound:
            continue
        local_name = str(node.attrs.get("address", "")).split(".")[-1].lower()
        graph.add_unresolved({
            "reason": "unbound_iac_resource",
            "id": nid,
            "hint": "declare a binding (repository, address, target ARM id) in the manifest",
            # Listed for the human, never linked: same name is not same resource.
            "name_candidates": sorted(by_name.get(local_name, [])),
        })


def _ambiguous_names(graph: Graph) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for nid, node in graph.nodes.items():
        name = node.attrs.get("name")
        if node.layer == "azure" and isinstance(name, str) and name:
            groups.setdefault(name.lower(), []).append(nid)
    return [
        {"name": name, "ids": sorted(ids), "linked": False}
        for name, ids in sorted(groups.items())
        if len(ids) > 1
    ]


__all__ = ["FederationResult", "federate"]
