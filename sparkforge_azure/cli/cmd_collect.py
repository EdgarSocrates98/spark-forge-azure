"""``sparkforge-azure collect workspace-graph|resource-graph`` (read-only).

Offline by default (ingest exports).  Reading the cloud requires the explicit
``--live`` flag and the ``azure`` extra; without it the command refuses
(exit 2) instead of silently degrading.  Everything printed or written has
passed redaction + ``assert_clean``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sparkforge_azure.cli.main import CliError
from sparkforge_azure.collectors import resource_graph
from sparkforge_azure.collectors.base import CollectorInputError, CollectorUnavailable
from sparkforge_azure.collectors.redact import RedactionError
from sparkforge_azure.collectors.workspace_graph import collect_workspace_graph
from sparkforge_azure.graph import Graph, WorkspaceError, save_graph


def _workspace_graph(args: argparse.Namespace) -> dict[str, Any]:
    if not args.live and not args.export:
        raise CliError("offline mode needs --export; cloud read requires explicit --live")
    try:
        result = collect_workspace_graph(
            args.manifest, export=None if args.live else args.export, live=args.live,
            hash_principals=args.hash_principals,
        )
    except (CollectorUnavailable, CollectorInputError, WorkspaceError, RedactionError,
            OSError) as exc:
        raise CliError(str(exc)) from exc
    graph = Graph.from_dict(result.pop("graph"))
    result["stats"] = graph.stats()
    result["unresolved"] = graph.unresolved
    if args.out:
        result["path"] = Path(args.out).as_posix()
        result["fingerprint"] = save_graph(graph, args.out)
    return result


def _resource_graph(args: argparse.Namespace) -> dict[str, Any]:
    try:
        res = resource_graph.from_export(args.export, hash_principals=args.hash_principals)
    except (CollectorInputError, RedactionError, OSError) as exc:
        raise CliError(str(exc)) from exc
    graph = resource_graph.to_graph(res)
    out: dict[str, Any] = {
        "status": "ok",
        "mode": res.mode,
        "records": res.records,
        "facts": len(res.facts),
        "redaction": res.redaction.to_dict(),
        "unresolved": res.unresolved,
        "stats": graph.stats(),
    }
    if args.out:
        out["path"] = Path(args.out).as_posix()
        out["fingerprint"] = save_graph(graph, args.out)
    if args.facts:
        out["fact_list"] = res.to_dict()["facts"]
    return out


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("collect", help="read-only Azure collectors (offline exports by default)")
    s = p.add_subparsers(dest="collect_cmd", metavar="<op>")

    w = s.add_parser("workspace-graph", help="live workspace graph for a manifest")
    w.add_argument("--manifest", required=True)
    w.add_argument("--export", help="offline Azure Resource Graph export (JSON)")
    w.add_argument("--live", action="store_true", help="read Azure (requires azure extra + auth)")
    w.add_argument("--out", help="write the live graph JSON here")
    w.add_argument("--hash-principals", action="store_true")
    w.set_defaults(func=_workspace_graph)

    r = s.add_parser("resource-graph", help="ingest an Azure Resource Graph export")
    r.add_argument("--export", required=True)
    r.add_argument("--out", help="write the live graph JSON here")
    r.add_argument("--facts", action="store_true", help="include the redacted facts")
    r.add_argument("--hash-principals", action="store_true")
    r.set_defaults(func=_resource_graph)
