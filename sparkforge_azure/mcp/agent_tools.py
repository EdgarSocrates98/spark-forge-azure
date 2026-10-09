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


@tool(
    "sfa_agents_runtimes",
    description=(
        "Runtime registry: per-runtime adapter, capabilities, proven status "
        "(declared/adapter_implemented/host_proven) and proof — §7 honesty."
    ),
    input_schema=_EMPTY,
    risk=READ_ONLY,
    domain="agentic",
    compact=True,
    output_schema={
        "type": "object",
        "required": ["runtimes"],
        "properties": {"runtimes": {"type": "object"}},
    },
)
def agents_runtimes(_: Mapping[str, Any]) -> dict[str, Any]:
    from sparkforge_azure.agentic.runtimes import runtime_registry

    return {
        "runtimes": {
            name.value: entry for name, entry in runtime_registry().items()
        }
    }


@tool(
    "sfa_agents_execution_explain",
    description=(
        "Planned execution for a prompt, dry-run only: route, planned stages, "
        "adapter status and execution mode. Never executes a host."
    ),
    input_schema={
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "runtime": {"type": "string", "default": "generic"},
        },
        "additionalProperties": False,
    },
    risk=READ_ONLY,
    domain="agentic",
    compact=True,
    output_schema={
        "type": "object",
        "required": ["route", "planned_stages", "execution_mode"],
        "properties": {
            "route": {"type": "array", "items": _ROUTE_ENTRY},
            "planned_stages": {"type": "array", "items": {"type": "string"}},
            "execution_mode": {"type": "string"},
            "adapter_status": {"type": "string"},
            "runtime": {"type": "string"},
        },
    },
)
def agents_execution_explain(args: Mapping[str, Any]) -> dict[str, Any]:
    from sparkforge_azure.agentic.pipeline import plan_pipeline
    from sparkforge_azure.agentic.runtime import RuntimeName
    from sparkforge_azure.agentic.runtimes import get_adapter

    prompt = str(args["prompt"])
    try:
        rt = RuntimeName(str(args.get("runtime") or "generic"))
    except ValueError:
        rt = RuntimeName.GENERIC
    adapter = get_adapter(rt)
    routed = explain_route(prompt)
    selected = [r["specialist"] for r in routed if r["decision"] == "selected"]
    stages: list[str] = []
    for spec in selected or [None]:
        stages.extend(plan_pipeline(specialist_id=spec))
    return {
        "runtime": rt.value,
        "adapter_status": adapter.status,
        "execution_mode": adapter.execution_mode,
        "route": routed,
        "planned_stages": sorted(set(stages)),
    }
