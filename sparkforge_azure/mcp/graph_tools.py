"""MCP tools for Graphfy (query, impact) and the workspace-graph collector.

``sfa_graph_query`` / ``sfa_graph_impact`` are READ_ONLY and offline.
``sfa_collect_workspace_graph`` is CLOUD_READ: the default-deny gate refuses it
unless cloud read is enabled -- even though its default path is an offline
export -- because it can read Azure when ``live`` is true.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.graph import find_nodes, impact, load_graph, neighbors
from sparkforge_azure.mcp.tools import CLOUD_READ, READ_ONLY, tool
from sparkforge_azure.paths import resolve_within


def _safe_path(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    resolved = resolve_within(Path.cwd(), value)
    if resolved is None:
        raise ValueError("path escapes the working directory")
    return resolved


@tool(
    "sfa_graph_query",
    description=("Query a Graphfy graph JSON: nodes by kind/layer, or neighbors of a node id "
                 "(optional relation/direction). Deterministic, bounded by limit."),
    input_schema={
        "type": "object",
        "properties": {
            "graph": {"type": "string"},
            "kind": {"type": "string"},
            "layer": {"type": "string"},
            "neighbors": {"type": "string"},
            "relation": {"type": "string"},
            "direction": {"type": "string", "enum": ["out", "in", "both"]},
            "limit": {"type": "integer", "minimum": 1, "maximum": 500},
        },
        "required": ["graph"],
        "additionalProperties": False,
    },
    risk=READ_ONLY, domain="graph",
    output_schema={
        "type": "object",
        "required": ["total"],
        "properties": {
            "total": {"type": "integer"},
            "nodes": {"type": "array"},
            "neighbors": {"type": "array"},
            "node": {"type": "string"},
        },
    },
)
def graph_query(args: Mapping[str, Any]) -> dict[str, Any]:
    graph = load_graph(_safe_path(args["graph"]))
    limit = int(args.get("limit", 100))
    if args.get("neighbors"):
        items = neighbors(graph, args["neighbors"], relation=args.get("relation"),
                          direction=args.get("direction", "out"))
        return {"node": args["neighbors"], "neighbors": items[:limit], "total": len(items)}
    nodes = find_nodes(graph, kind=args.get("kind"), layer=args.get("layer"))
    return {"nodes": [n.to_dict() for n in nodes[:limit]], "total": len(nodes)}


@tool(
    "sfa_graph_impact",
    description=("Change impact over a Graphfy graph: dependents of changed files/symbols/"
                 "knowledge ids grouped by category (symbols, callers, tests, configs, rules, "
                 "skills, agents, knowledge, resources, data) + unresolved. Depth-bounded."),
    input_schema={
        "type": "object",
        "properties": {
            "graph": {"type": "string"},
            "changed": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "max_depth": {"type": "integer", "minimum": 0, "maximum": 8},
        },
        "required": ["graph", "changed"],
        "additionalProperties": False,
    },
    risk=READ_ONLY, domain="graph", compact=True,
    output_schema={"type": "object"},
)
def graph_impact(args: Mapping[str, Any]) -> dict[str, Any]:
    graph = load_graph(_safe_path(args["graph"]))
    return impact(graph, list(args["changed"]), max_depth=int(args.get("max_depth", 3)))


@tool(
    "sfa_collect_workspace_graph",
    description=("Build the live workspace graph for a sparkforge-azure.workspace.yaml from an "
                 "Azure Resource Graph export (offline) or Azure itself (live=true). Read-only, "
                 "redacted, scoped to declared subscriptions."),
    input_schema={
        "type": "object",
        "properties": {
            "manifest": {"type": "string"},
            "export": {"type": "string"},
            "live": {"type": "boolean"},
        },
        "required": ["manifest"],
        "additionalProperties": False,
    },
    risk=CLOUD_READ, domain="graph",
    output_schema={"type": "object"},
)
def collect_workspace_graph_tool(args: Mapping[str, Any]) -> dict[str, Any]:
    from sparkforge_azure.collectors.workspace_graph import collect_workspace_graph

    export = args.get("export")
    return collect_workspace_graph(
        _safe_path(args["manifest"]),
        export=_safe_path(export) if export else None,
        live=bool(args.get("live", False)),
    )
