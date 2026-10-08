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
from sparkforge_azure.collectors import adls_meta, azure_rbac, resource_graph, unity_catalog
from sparkforge_azure.collectors.base import CollectorInputError, CollectorUnavailable
from sparkforge_azure.collectors.recover import collect_with_recovery
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


def _access_collector(module: Any, label: str) -> Any:
    def _run(args: argparse.Namespace) -> dict[str, Any]:
        if not args.live and not args.export:
            raise CliError(f"{label}: offline needs --export; cloud read requires --live")
        try:
            if args.live:
                kwargs = {k: v for k, v in vars(args).items()
                          if k in getattr(module, "LIVE_ARGS", ())}
                missing = [k for k in getattr(module, "LIVE_ARGS", ())
                           if kwargs.get(k) in (None, "") and k != "subscription_id"]
                if missing:
                    flags = ", ".join("--" + m.replace("_", "-") for m in missing)
                    raise CliError(f"{label} --live needs: {flags}")
                outcome = collect_with_recovery(
                    module.collect_live, kwargs=kwargs,
                    offline_export=args.fallback_export,
                    from_export=module.from_export, source=label)
                res = outcome["result"]
                if res is None:
                    raise CliError(
                        f"{label}: live collection unresolved "
                        f"({outcome['unresolved'][0]['failure_class']}); "
                        "no offline export to fall back to")
                extra = {"degraded": outcome["status"] == "degraded",
                         "recovery": {"status": outcome["status"],
                                      "decisions": outcome["decisions"],
                                      "receipt": outcome["receipt"]}}
            else:
                res = module.from_export(args.export)
                extra = {}
        except (CollectorUnavailable, CollectorInputError, RedactionError,
                OSError) as exc:
            raise CliError(str(exc)) from exc
        return {"status": "ok", "source": res.source, "mode": res.mode,
                "records": res.records, "facts": len(res.facts),
                "redaction": res.redaction.to_dict(), "unresolved": res.unresolved,
                "fact_list": res.to_dict()["facts"] if args.facts else [],
                **extra}
    return _run


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

    uc = s.add_parser("unity-catalog", help="UC credentials/locations/catalogs/grants")
    uc.add_argument("--export", help="offline UC export (JSON)")
    uc.add_argument("--live", action="store_true",
                    help="read the workspace via databricks-sdk")
    uc.add_argument("--host", help="workspace URL (with --live)")
    uc.add_argument("--workspace-id", help="numeric workspace id (with --live)")
    uc.add_argument("--fallback-export",
                    help="offline export to use if --live fails (degraded mode)")
    uc.add_argument("--facts", action="store_true")
    uc.set_defaults(func=_access_collector(unity_catalog, "unity-catalog"))

    rb = s.add_parser("azure-rbac", help="role assignments at a scope")
    rb.add_argument("--export", help="offline assignments export (JSON)")
    rb.add_argument("--live", action="store_true",
                    help="read assignments via azure-mgmt-authorization")
    rb.add_argument("--scope", help="ARM scope to list assignments for (--live)")
    rb.add_argument("--subscription-id", help="subscription for --live")
    rb.add_argument("--fallback-export",
                    help="offline export to use if --live fails (degraded mode)")
    rb.add_argument("--facts", action="store_true")
    rb.set_defaults(func=_access_collector(azure_rbac, "azure-rbac"))

    ad = s.add_parser("adls-meta", help="ADLS account posture + ACLs")
    ad.add_argument("--export", help="offline ADLS export (JSON)")
    ad.add_argument("--live", action="store_true",
                    help="read ACLs via azure-storage-file-datalake")
    ad.add_argument("--account-url", help="https://<acct>.dfs.core.windows.net")
    ad.add_argument("--container", help="filesystem/container name")
    ad.add_argument("--paths", nargs="*", help="paths whose ACLs to read")
    ad.add_argument("--fallback-export",
                    help="offline export to use if --live fails (degraded mode)")
    ad.add_argument("--facts", action="store_true")
    ad.set_defaults(func=_access_collector(adls_meta, "adls-meta"))
