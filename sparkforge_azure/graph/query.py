"""Deterministic Graphfy queries.

All results are sorted; traversals are bounded (depth and/or node budget) so
a query never returns more context than asked for (context minimality).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

from sparkforge_azure.graph.model import Graph, GraphError, Node


def find_nodes(
    graph: Graph,
    *,
    kind: str | None = None,
    layer: str | None = None,
    attrs: dict[str, Any] | None = None,
    limit: int | None = None,
) -> list[Node]:
    out = []
    for nid in sorted(graph.nodes):
        node = graph.nodes[nid]
        if kind is not None and node.kind != kind:
            continue
        if layer is not None and node.layer != layer:
            continue
        if attrs and any(node.attrs.get(k) != v for k, v in attrs.items()):
            continue
        out.append(node)
        if limit is not None and len(out) >= limit:
            break
    return out


def neighbors(
    graph: Graph,
    nid: str,
    *,
    relation: str | Iterable[str] | None = None,
    direction: str = "out",
) -> list[dict[str, Any]]:
    """Neighbors with the relation that links them (sorted)."""

    if nid not in graph.nodes:
        raise GraphError(f"unknown node: {nid}")
    rels = {relation} if isinstance(relation, str) else (set(relation) if relation else None)
    out: list[dict[str, Any]] = []
    for (src, rel, dst) in sorted(graph.edges):
        if rels is not None and rel not in rels:
            continue
        if direction in ("out", "both") and src == nid:
            out.append({"id": dst, "relation": rel, "direction": "out"})
        if direction in ("in", "both") and dst == nid:
            out.append({"id": src, "relation": rel, "direction": "in"})
    return out


def shortest_path(
    graph: Graph,
    source: str,
    target: str,
    *,
    max_depth: int = 6,
    relations: Iterable[str] | None = None,
    directed: bool = False,
) -> list[str] | None:
    """Bounded BFS; ties broken by sorted neighbor order (deterministic)."""

    if source not in graph.nodes or target not in graph.nodes:
        return None
    if source == target:
        return [source]
    rels = set(relations) if relations else None
    adj: dict[str, set[str]] = {}
    for (src, rel, dst) in graph.edges:
        if rels is not None and rel not in rels:
            continue
        adj.setdefault(src, set()).add(dst)
        if not directed:
            adj.setdefault(dst, set()).add(src)
    prev: dict[str, str] = {}
    queue: deque[tuple[str, int]] = deque([(source, 0)])
    seen = {source}
    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for nxt in sorted(adj.get(current, ())):
            if nxt in seen:
                continue
            seen.add(nxt)
            prev[nxt] = current
            if nxt == target:
                path = [target]
                while path[-1] != source:
                    path.append(prev[path[-1]])
                return list(reversed(path))
            queue.append((nxt, depth + 1))
    return None


def slice_graph(
    graph: Graph,
    seeds: Iterable[str],
    *,
    budget: int = 50,
    max_depth: int = 2,
    relations: Iterable[str] | None = None,
) -> tuple[Graph, bool]:
    """Undirected BFS slice around ``seeds`` limited by a node ``budget``.

    Returns ``(subgraph, truncated)``.  Seeds are always included first.
    """

    if budget < 1:
        raise GraphError("budget must be >= 1")
    rels = set(relations) if relations else None
    adj: dict[str, set[str]] = {}
    for (src, rel, dst) in graph.edges:
        if rels is not None and rel not in rels:
            continue
        adj.setdefault(src, set()).add(dst)
        adj.setdefault(dst, set()).add(src)
    keep: list[str] = []
    for s in sorted(set(seeds)):
        if s in graph.nodes and len(keep) < budget:
            keep.append(s)
    truncated = len([s for s in set(seeds) if s in graph.nodes]) > len(keep)
    queue: deque[tuple[str, int]] = deque((s, 0) for s in keep)
    kept = set(keep)
    while queue and not truncated:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for nxt in sorted(adj.get(current, ())):
            if nxt in kept or nxt not in graph.nodes:
                continue
            if len(kept) >= budget:
                truncated = True
                break
            kept.add(nxt)
            queue.append((nxt, depth + 1))
    sub = graph.subgraph(kept)
    sub.meta = {**graph.meta, "slice": {"seeds": sorted(set(seeds)), "budget": budget,
                                        "max_depth": max_depth, "truncated": truncated}}
    return sub, truncated


__all__ = ["find_nodes", "neighbors", "shortest_path", "slice_graph"]
