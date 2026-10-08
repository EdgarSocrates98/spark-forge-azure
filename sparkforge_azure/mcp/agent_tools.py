"""Read-only agent fleet inspection tools (SDD MCP_AGENT_ADMIN).

Two verbs, no more — §147-148 asks for agent control via MCP without bloat.
Both handlers call the same engines as the CLI (``inventory()`` and
``explain_route()``); nothing here mutates, spawns or touches the cloud.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.inventory import inventory
from sparkforge_azure.agentmanifest.routing import explain_route
from sparkforge_azure.mcp.tools import READ_ONLY, tool

_EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}

_AGENT_ENTRY = {
    "type": "object",
    "required": ["agent_id", "kind", "status"],
    "properties": {
        "agent_id": {"type": "string"},
        "kind": {"type": "string"},
        "status": {"type": "string"},
    },
}

_ROUTE_ENTRY = {
    "type": "object",
    "required": ["specialist", "decision"],
    "properties": {
        "specialist": {"type": "string"},
        "matched_terms": {"type": "array", "items": {"type": "string"}},
        "score": {"type": "integer"},
        "decision": {"type": "string"},
        "reason": {"type": "string"},
    },
}


@tool(
    "sfa_agents_list",
    description="Agent fleet inventory: every agent with its closed status.",
    input_schema=_EMPTY,
    risk=READ_ONLY,
    domain="agentic",
    compact=True,
    output_schema={
        "type": "object",
        "required": ["agents", "counts"],
        "properties": {
            "agents": {"type": "array", "items": _AGENT_ENTRY},
            "counts": {"type": "object"},
        },
    },
)
def agents_list(_: Mapping[str, Any]) -> dict[str, Any]:
    rep = inventory(Path.cwd())
    return {
        "agents": [
            {"agent_id": a.agent_id, "kind": a.kind, "status": a.status}
            for a in rep.agents
        ],
        "counts": dict(rep.counts),
    }


@tool(
    "sfa_agents_explain_route",
    description=(
        "Explain the deterministic specialist route for a prompt: per-specialist "
        "decision (selected/below_cap/no_match), matched terms and reason."
    ),
    input_schema={
        "type": "object",
        "required": ["prompt"],
        "properties": {"prompt": {"type": "string"}},
        "additionalProperties": False,
    },
    risk=READ_ONLY,
    domain="agentic",
    compact=True,
    output_schema={
        "type": "object",
        "required": ["route"],
        "properties": {"route": {"type": "array", "items": _ROUTE_ENTRY}},
    },
)
def agents_explain_route(args: Mapping[str, Any]) -> dict[str, Any]:
    return {"route": explain_route(str(args["prompt"]))}
