"""``sparkforge-azure agentops`` — inspect recorded runs (prompt #106-108).

Reads ``.sparkforge-azure/traces.db`` (or ``--db``): runs, per-run span
inspection with waste attributions, ordered timeline and the temporal
critical-path approximation.  Read-only; never mutates state.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sparkforge_azure.cli import CliError
from sparkforge_azure.observability import agentops
from sparkforge_azure.observability.store import SQLiteTraceStore


def _db(args: argparse.Namespace) -> Path:
    return Path(args.db).expanduser().resolve() if args.db else (
        Path.cwd() / ".sparkforge-azure" / "traces.db")


def _run_id(args: argparse.Namespace) -> str:
    if args.run:
        return args.run
    runs = SQLiteTraceStore(_db(args)).list_runs(limit=1)
    if not runs:
        raise CliError("no recorded runs; run a command first "
                       "(spans land in .sparkforge-azure/traces.db)")
    return str(runs[0]["run_id"])


def _runs(args: argparse.Namespace) -> dict[str, Any]:
    db = _db(args)
    if not db.is_file():
        raise CliError(f"trace db not found: {db}")
    return {"status": "ok", "runs": SQLiteTraceStore(db).list_runs(
        limit=args.limit)}


def _inspect(args: argparse.Namespace) -> dict[str, Any]:
    return agentops.inspect_run(_db(args), _run_id(args))


def _timeline(args: argparse.Namespace) -> dict[str, Any]:
    return agentops.run_timeline(_db(args), _run_id(args))


def _critical(args: argparse.Namespace) -> dict[str, Any]:
    return agentops.critical_path(_db(args), _run_id(args))


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("agentops", help="inspect recorded runs: "
                       "runs/inspect/timeline/critical-path")
    p.add_argument("--db", default=None,
                   help="traces.db path (default ./.sparkforge-azure/traces.db)")
    s = p.add_subparsers(dest="agentops_action", metavar="<op>")
    s.required = True
    q = s.add_parser("runs", help="list recorded runs")
    q.add_argument("--limit", type=int, default=20)
    q.set_defaults(func=_runs)
    for op, fn in (("inspect", _inspect), ("timeline", _timeline),
                   ("critical-path", _critical)):
        q = s.add_parser(op)
        q.add_argument("--run", default=None,
                       help="run_id (default: most recent)")
        q.set_defaults(func=fn)
