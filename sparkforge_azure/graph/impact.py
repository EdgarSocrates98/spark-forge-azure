"""Change impact over a Graphfy graph (section 54).

Given changed files, symbols, knowledge ids or node ids, walk the dependents
with a depth bound and group them: symbols, callers, tests, configs, rules, skills,
agents, knowledge, resources, data, files.  A changed item that does not
resolve to a node by exact id/path is returned in ``unresolved`` -- never
matched by a similar name.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

from sparkforge_azure.graph.model import Graph

# relation -> who depends on whom.  "reverse": the edge SOURCE depends on the
# target (A imports B: changing B impacts A).  "forward": the edge TARGET
# depends on the source (file defines symbol: changing the file impacts it).
DEPENDENCY_DIRECTION: dict[str, str] = {
    "imports": "reverse",
    "calls": "reverse",
    "tests": "reverse",
    "configures": "reverse",
    "references": "reverse",
    "refers_knowledge": "reverse",
    "uses_skill": "reverse",
    "related": "reverse",
    "depends_on": "reverse",
    "runs_in": "reverse",
    "located_in": "reverse",
    "member_of": "reverse",
    # access graph relations (graph/access.py): the source depends on target
    "accesses": "reverse",
    "applies_to": "reverse",
    "bound_to": "reverse",
    "executes": "reverse",
    "has_privilege": "reverse",
    "has_role": "reverse",
    "located_at": "reverse",
    "part_of": "reverse",
    "points_to": "reverse",
    "reads": "reverse",
    "uses": "reverse",
    "uses_identity": "reverse",
    "writes": "reverse",
    "defines": "forward",
    "contains": "forward",
    "binds_to": "forward",
    "exposes_identity": "forward",
    "same_as": "both",
    "governs": "both",
}

CATEGORIES = (
    "symbols", "callers", "tests", "configs", "rules", "skills", "agents", "knowledge",
    "resources", "data", "files", "other",
)


def category_of(graph: Graph, nid: str) -> str:
    node = graph.nodes.get(nid)
    if node is None:
        return "other"
    if node.layer == "azure":
        return "resources"
    if node.layer == "data":
        return "data"
    if node.layer == "knowledge":
        return {"skill": "skills", "agent": "agents", "rule": "rules",
                "boundary": "rules"}.get(node.kind, "knowledge")
    if node.kind == "test":
        return "tests"
    if node.kind == "config":
        return "configs"
    if node.kind in ("function", "class", "symbol"):
        return "callers"
    if node.kind in ("file", "repository"):
        return "files"
    return "other"


def resolve_changed(graph: Graph, item: str) -> list[str]:
    """Exact resolution only: node id, knowledge id, ``repo/path`` or ``path``."""

    value = item.strip().replace("\\", "/")
    if value in graph.nodes:
        return [value]
    hits = []
    for nid, node in sorted(graph.nodes.items()):
        path = node.attrs.get("path")
        repo = node.attrs.get("repo") or ""
        if node.kind in ("file", "test", "config") and isinstance(path, str):
            if value == path or (repo and value == f"{repo}/{path}"):
                hits.append(nid)
        elif node.layer == "knowledge" and node.attrs.get("id") == value:
            hits.append(nid)
        elif node.attrs.get("qualified_name") and value == (
            f"{path}::{node.attrs['qualified_name']}"
        ):
            hits.append(nid)
    return hits


def dependents(graph: Graph, nid: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for (src, rel, dst) in sorted(graph.edges):
        direction = DEPENDENCY_DIRECTION.get(rel)
        if direction is None:
            continue
        if direction in ("reverse", "both") and dst == nid:
            out.append((src, rel))
        if direction in ("forward", "both") and src == nid:
            out.append((dst, rel))
    return out


def impact(
    graph: Graph,
    changed: Iterable[str],
    *,
    max_depth: int = 3,
    max_nodes: int = 500,
) -> dict[str, Any]:
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    seeds: list[str] = []
    unresolved: list[dict[str, Any]] = []
    for item in changed:
        hits = resolve_changed(graph, item)
        if not hits:
            unresolved.append({"changed": item, "reason": "not_in_graph"})
        seeds.extend(h for h in hits if h not in seeds)
    # adjacency built once (deterministic)
    adj: dict[str, list[tuple[str, str]]] = {}
    for (src, rel, dst) in sorted(graph.edges):
        direction = DEPENDENCY_DIRECTION.get(rel)
        if direction in ("reverse", "both"):
            adj.setdefault(dst, []).append((src, rel))
        if direction in ("forward", "both"):
            adj.setdefault(src, []).append((dst, rel))
    seen: dict[str, dict[str, Any]] = {}
    queue: deque[tuple[str, int]] = deque((s, 0) for s in seeds)
    visited = set(seeds)
    truncated = False
    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for nxt, rel in adj.get(current, []):
            if nxt in visited:
                continue
            if len(seen) >= max_nodes:
                truncated = True
                break
            visited.add(nxt)
            seen[nxt] = {"id": nxt, "depth": depth + 1, "via": rel, "from": current}
            queue.append((nxt, depth + 1))
    seed_set = set(seeds)
    calls_out: dict[str, list[str]] = {}
    for (src, rel, dst) in graph.edges:
        if rel == "calls":
            calls_out.setdefault(src, []).append(dst)
    grouped: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
    for nid in sorted(seen, key=lambda n: (seen[n]["depth"], n)):
        cat = category_of(graph, nid)
        entry = seen[nid]
        if cat == "callers" and entry["via"] in ("defines", "contains"):
            # defined by a changed item -> "symbols"; reached through its file but
            # calling something impacted -> a real caller.
            calls_impacted = any(t in seen or t in seed_set for t in calls_out.get(nid, ()))
            if entry["from"] in seed_set or not calls_impacted:
                cat = "symbols"
        grouped[cat].append(seen[nid])
    return {
        "changed": sorted(seeds),
        "impacted": {k: v for k, v in grouped.items() if v},
        "counts": {k: len(v) for k, v in grouped.items() if v},
        "total": len(seen),
        "max_depth": max_depth,
        "truncated": truncated,
        "unresolved": unresolved,
    }


__all__ = ["CATEGORIES", "DEPENDENCY_DIRECTION", "category_of", "dependents", "impact",
           "resolve_changed"]
