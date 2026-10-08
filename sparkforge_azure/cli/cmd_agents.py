"""``sparkforge-azure agents`` -- agent fleet inspection.

  * ``agents list``      — every agent in the taxonomy with its status
    (ready | partial | manifest_only | broken | unevaluated) + counts
  * ``agents inspect <id>`` — full contract report for one agent

The engine is `sparkforge_azure.agentic.inventory.inventory` — a pure
function of the repository tree. These verbs are the inspection surface;
nothing here executes an agent.
"""
from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.agentic.inventory import get_agent, inventory
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


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "agents",
        help="agent fleet — list status, inspect one contract",
    )
    inner = p.add_subparsers(dest="agents_op")

    lp = inner.add_parser("list", help="status of every agent in the taxonomy")
    lp.set_defaults(func=_list)

    ip = inner.add_parser("inspect", help="full contract report for one agent")
    ip.add_argument("agent_id")
    ip.set_defaults(func=_inspect)
