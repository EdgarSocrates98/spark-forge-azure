"""Bounded, deterministic queries over the access graph (P0-C).

Five high-value questions, all answered by bounded traversal with explicit
budgets -- never by scanning the whole graph and never by name similarity:

* ``who_can_access``       -- principals that reach a storage/table target
* ``jobs_depending_on``    -- jobs (via notebooks/tables) bound to a location
* ``what_breaks_if_changed`` -- impact cone via ``graph.impact``
* ``tables_of_credential`` -- tables located under a storage credential
* ``repo_defining``        -- IaC repos that declare an Azure resource
"""
from __future__ import annotations

from collections import deque
from typing import Any

from sparkforge_azure.graph.access import ACCESS_RELATIONS
from sparkforge_azure.graph.impact import impact
from sparkforge_azure.graph.model import Graph

# Relations where the SOURCE object depends on the TARGET (table located_at
# location: the table breaks if the location is repointed).
_DEPENDENT_RELATIONS = frozenset({
    "located_at", "reads", "writes", "accesses", "executes", "uses",
    "has_privilege", "governs", "bound_to", "uses_identity",
})

_IDENTITY_PREFIXES = ("azure:identity:", "azure:/subscriptions/")


def _require_node(graph: Graph, nid: str) -> None:
    if nid not in graph.nodes:
        raise ValueError(f"node not in access graph: {nid!r}")


def _bfs_in(graph: Graph, seed: str, relations: frozenset[str],
            *, max_nodes: int, max_depth: int) -> tuple[list[str], bool]:
    """Reverse-direction BFS: who depends on ``seed`` via ``relations``."""
    seen: list[str] = []
    visited = {seed}
    queue: deque[tuple[str, int]] = deque([(seed, 0)])
    truncated = False
    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for edge in graph.in_edges(current):
            if edge.relation not in relations or edge.source in visited:
                continue
            if len(seen) >= max_nodes:
                return seen, True
            visited.add(edge.source)
            seen.append(edge.source)
            queue.append((edge.source, depth + 1))
    seen.sort()
    return seen, truncated


def _bfs_both(graph: Graph, seed: str, relations: frozenset[str],
              *, max_nodes: int, max_depth: int) -> tuple[list[str], bool]:
    seen: list[str] = []
    visited = {seed}
    queue: deque[tuple[str, int]] = deque([(seed, 0)])
    truncated = False
    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        edges = [(e.source, e) for e in graph.in_edges(current)
                 if e.relation in relations]
        edges += [(e.target, e) for e in graph.out_edges(current)
                  if e.relation in relations]
        for nxt, _edge in edges:
            if nxt in visited:
                continue
            if len(seen) >= max_nodes:
                return seen, True
            visited.add(nxt)
            seen.append(nxt)
            queue.append((nxt, depth + 1))
    seen.sort()
    return seen, truncated


def who_can_access(graph: Graph, target: str, *, max_depth: int = 6,
                   max_nodes: int = 200) -> dict[str, Any]:
    """Principals (identities) that reach ``target`` through access relations."""
    _require_node(graph, target)
    reached, truncated = _bfs_both(graph, target, ACCESS_RELATIONS,
                                   max_nodes=max_nodes, max_depth=max_depth)
    principals = sorted(
        n for n in reached
        if n.startswith(_IDENTITY_PREFIXES)
        and graph.nodes[n].kind == "identity"
    )
    return {
        "target": target,
        "principals": principals,
        "reached": reached,
        "budget": max_nodes,
        "max_depth": max_depth,
        "truncated": truncated,
    }


def jobs_depending_on(graph: Graph, location: str, *, max_depth: int = 6,
                      max_nodes: int = 200) -> dict[str, Any]:
    """Jobs that reach ``location`` via table->notebook->job chains."""
    if location not in graph.nodes:
        return {"location": location, "jobs": [], "via_notebooks": [],
                "unresolved": [{"reason": "not_in_graph", "id": location}],
                "truncated": False}
    reached, truncated = _bfs_in(graph, location, _DEPENDENT_RELATIONS,
                                 max_nodes=max_nodes, max_depth=max_depth)
    jobs = sorted(n for n in reached if graph.nodes[n].kind == "job")
    notebooks = sorted(n for n in reached if graph.nodes[n].kind == "notebook")
    return {
        "location": location,
        "jobs": jobs,
        "via_notebooks": notebooks,
        "unresolved": [],
        "truncated": truncated,
    }


def what_breaks_if_changed(graph: Graph, node_id: str, *, max_depth: int = 3,
                           max_nodes: int = 500) -> dict[str, Any]:
    """Impact cone of a change at ``node_id`` (delegates to graph.impact)."""
    _require_node(graph, node_id)
    return impact(graph, [node_id], max_depth=max_depth, max_nodes=max_nodes)


def tables_of_credential(graph: Graph, credential: str, *,
                         max_nodes: int = 200) -> dict[str, Any]:
    """Tables under external locations that use ``credential``."""
    _require_node(graph, credential)
    locations = sorted(e.source for e in graph.in_edges(credential)
                       if e.relation == "uses")
    tables: set[str] = set()
    truncated = len(locations) > max_nodes
    for loc in locations[:max_nodes]:
        for e in graph.in_edges(loc):
            if e.relation == "located_at" and len(tables) < max_nodes:
                tables.add(e.source)
    return {
        "credential": credential,
        "via_locations": locations[:max_nodes],
        "tables": sorted(tables),
        "truncated": truncated,
    }


def repo_defining(graph: Graph, node_id: str, *,
                  max_nodes: int = 50) -> dict[str, Any]:
    """Repositories whose code layer binds to ``node_id`` (explicit binding)."""
    _require_node(graph, node_id)
    repos: set[str] = set()
    sources: list[str] = []
    for e in graph.in_edges(node_id):
        if e.relation != "binds_to" or len(sources) >= max_nodes:
            continue
        src = graph.nodes.get(e.source)
        if src is None:
            continue
        sources.append(e.source)
        repo = src.attrs.get("repo")
        if repo:
            repos.add(str(repo))
    unresolved = [] if sources else [
        {"reason": "no_explicit_binding", "id": node_id}
    ]
    return {
        "node": node_id,
        "repos": sorted(repos),
        "bindings": sorted(sources),
        "unresolved": unresolved,
    }


__all__ = [
    "who_can_access", "jobs_depending_on", "what_breaks_if_changed",
    "tables_of_credential", "repo_defining",
]
