"""``sparkforge-azure agents`` -- agent fleet inspection.

  * ``agents list``      — every agent in the taxonomy with its status
    (ready | partial | manifest_only | broken | unevaluated) + counts
  * ``agents inspect <id>`` — full contract report for one agent
  * ``agents route <query>`` — deterministic route explanation + the spawn
    gate (SPAWN | SKIP | DEFER) per specialist
  * ``agents fingerprint`` — deterministic hash over the fleet's contract
  * ``agents impact --path X`` — agents/evals/tests a changed path invalidates

The engines are `sparkforge_azure.agentic.{inventory,fingerprint,impact}`
and `agentmanifest.routing.explain_route` — pure functions.
Nothing here executes an agent.
"""
from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.agentic.fingerprint import fleet_fingerprint
from sparkforge_azure.agentic.impact import impact_for
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


def _fingerprint(args: argparse.Namespace) -> dict[str, Any]:
    return {"status": "ok", **fleet_fingerprint(".")}


def _impact(args: argparse.Namespace) -> dict[str, Any]:
    report = impact_for(args.path)
    status = "unresolved" if report["unresolved"] else "ok"
    return {"status": status, **report}


def _runtimes(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.agentic.runtimes import runtime_registry

    reg = runtime_registry()
    return {
        "status": "ok",
        "runtimes": {
            name.value: {
                "adapter": e["adapter"],
                "status": e["status"],
                "proof": e["proof"],
                "spawn_agent": e["capabilities"]["spawn_agent"],
            }
            for name, e in reg.items()
        },
    }


def _runtime_inspect(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.agentic.runtime import RuntimeName
    from sparkforge_azure.agentic.runtimes import runtime_registry

    try:
        name = RuntimeName(args.runtime)
    except ValueError:
        raise CliError(f"runtime desconhecido: {args.runtime}") from None
    entry = runtime_registry()[name]
    return {"status": "ok", "runtime": name.value, **entry}


def _execute(args: argparse.Namespace) -> dict[str, Any]:
    """§148-150 — dry-run: route + plan + budgets + mode, SEM host."""
    from sparkforge_azure.agentic.execution import stage_fingerprint
    from sparkforge_azure.agentic.pipeline import plan_pipeline
    from sparkforge_azure.agentic.runtime import RuntimeName
    from sparkforge_azure.agentic.runtimes import get_adapter

    try:
        rt = RuntimeName(args.runtime)
    except ValueError:
        raise CliError(f"runtime desconhecido: {args.runtime}") from None
    adapter = get_adapter(rt)
    routed = explain_route(args.task, max_agents=args.max_agents)
    selected = [r["specialist"] for r in routed if r["decision"] == "selected"]
    stages: list[str] = []
    for spec in selected or [None]:
        stages.extend(plan_pipeline(specialist_id=spec))
    case = {"id": "dry-run", "task": args.task}
    return {
        "status": "ok",
        "dry_run": True,
        "runtime": rt.value,
        "adapter_status": adapter.status,
        "execution_mode": adapter.execution_mode,
        "route": routed,
        "planned_stages": sorted(set(stages)),
        "stage_fingerprints": {
            s: stage_fingerprint(s, case, rt, ".") for s in sorted(set(stages))
        },
        "note": "dry-run — nenhum host executado (§149)",
    }


def _compare(args: argparse.Namespace) -> dict[str, Any]:
    """§151 — configs A-D sobre o case; quality frontier."""
    from pathlib import Path

    import yaml

    from sparkforge_azure.agentic.agent_eval import evaluate_case

    case_path = Path(args.case)
    if not case_path.is_file():
        raise CliError(f"case nao encontrado: {args.case}")
    yaml.safe_load(case_path.read_text(encoding="utf-8"))  # validate
    out = evaluate_case(case_path)
    return {"status": "ok", **{k: out[k] for k in (
        "case_id", "runtime", "quality_frontier", "necessity")}}


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

    fp = inner.add_parser(
        "fingerprint",
        help="deterministic hash over the fleet's contract surface")
    fp.set_defaults(func=_fingerprint)

    xp = inner.add_parser(
        "impact",
        help="agents + test surfaces a changed path invalidates")
    xp.add_argument("--path", action="append", required=True,
                    help="repo-relative path changed (repeatable)")
    xp.set_defaults(func=_impact)

    rtp = inner.add_parser(
        "runtimes", help="runtime registry: adapter, status, proof")
    rtp.set_defaults(func=_runtimes)

    rip = inner.add_parser("runtime-inspect",
                           help="full registry entry for one runtime")
    rip.add_argument("runtime")
    rip.set_defaults(func=_runtime_inspect)

    ep = inner.add_parser(
        "execute", help="dry-run do plano de execucao (nunca executa host)")
    ep.add_argument("task", help="free-text case/task")
    ep.add_argument("--runtime", default="generic")
    ep.add_argument("--max-agents", type=int, default=3)
    ep.add_argument("--dry-run", action="store_true", default=True,
                    help="always on — host execution is opt-in elsewhere")
    ep.set_defaults(func=_execute)

    cp = inner.add_parser(
        "compare", help="A/B configs A-D over a case file -> frontier")
    cp.add_argument("case", help="path to evals/agent_runtime/cases/*.yaml")
    cp.set_defaults(func=_compare)
