"""``sparkforge-azure agents`` -- agent fleet inspection.

  * ``agents list``      — every agent in the taxonomy with its status
    (ready | partial | manifest_only | broken | unevaluated) + counts
  * ``agents inspect <id>`` — full contract report for one agent
  * ``agents route <query>`` — deterministic route explanation + the spawn
    gate (SPAWN | SKIP | DEFER) per specialist

The engines are `sparkforge_azure.agentic.inventory` and
`sparkforge_azure.agentmanifest.routing.explain_route` — pure functions.
Nothing here executes an agent.
"""
from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.agentic.inventory import get_agent, inventory
from sparkforge_azure.agentic.spawn import SpawnContext, decide_spawn
from sparkforge_azure.agentmanifest.routing import explain_route
from sparkforge_azure.cli import CliError


def _list(args: argparse.Namespace) -> dict[str, Any]:
    rep = inventory(".")
    return {
        "status": "ok",
        "counts": rep.counts,
        "agents": [
            {"agent_id": a.agent_id, "kind": a.kind, "status": a.status}
            for a in rep.agents
        ],
    }


def _inspect(args: argparse.Namespace) -> dict[str, Any]:
    rep = get_agent(".", args.agent_id)
    if rep is None:
        raise CliError(f"agent desconhecido: {args.agent_id}")
    return {"status": "ok", "agent": rep.to_dict()}


def _route(args: argparse.Namespace) -> dict[str, Any]:
    explained = explain_route(args.query, max_agents=args.max_agents)
    routed = [r["specialist"] for r in explained if r["decision"] == "selected"]
    unresolved = tuple(f"{a}:pending" for a in args.unresolved_domain or ())
    ctx = SpawnContext(
        routed_specialists=tuple(routed),
        unresolved=unresolved or tuple(f"{r}:domain" for r in routed),
    )
    spawn = {
        d.agent_id: {"decision": d.decision, "reason": d.reason,
                     "expected_gain": d.expected_gain}
        for d in (decide_spawn(r["specialist"], ctx) for r in explained)
    }
    return {
        "status": "ok",
        "query": args.query,
        "selected": routed,
        "candidates": explained,
        "spawn": spawn,
    }


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "agents",
        help="agent fleet — list status, inspect one contract, explain a route",
    )
    inner = p.add_subparsers(dest="agents_op")

    lp = inner.add_parser("list", help="status of every agent in the taxonomy")
    lp.set_defaults(func=_list)

    ip = inner.add_parser("inspect", help="full contract report for one agent")
    ip.add_argument("agent_id")
    ip.set_defaults(func=_inspect)

    rp = inner.add_parser(
        "route", help="deterministic route explanation + spawn gate per candidate")
    rp.add_argument("query", help="free-text task/problem to route")
    rp.add_argument("--max-agents", type=int, default=3,
                    help="specialist cap (1-5, default 3)")
    rp.add_argument("--unresolved-domain", action="append",
                    help="domain with an open unresolved item (repeatable)")
    rp.set_defaults(func=_route)
