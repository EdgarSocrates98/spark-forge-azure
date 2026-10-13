"""``sparkforge-azure graph build|query|impact|federate`` (Graphfy, offline).

Exit codes follow the CLI convention: 0 ok, 1 unresolved/blocked result,
2 refused input (``CliError``).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sparkforge_azure.cli.main import CliError
from sparkforge_azure.graph import (
    MANIFEST_NAME,
    Graph,
    GraphError,
    WorkspaceError,
    build_code_graph,
    build_incremental,
    federate,
    find_nodes,
    impact,
    knowledge_graph,
    load_graph,
    load_workspace_manifest,
    neighbors,
    save_graph,
    shortest_path,
)
from sparkforge_azure.graph.store import default_state_dir


def _load(path: str) -> Graph:
    try:
        return load_graph(path)
    except GraphError as exc:
        raise CliError(str(exc)) from exc


def _build(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise CliError(f"root is not a directory: {args.root}")
    manifest_path = Path(args.manifest) if args.manifest else root / MANIFEST_NAME
    report: dict[str, Any] = {}
    try:
        if args.manifest or manifest_path.is_file():
            manifest = load_workspace_manifest(manifest_path)
            graph, report = build_incremental(manifest, use_codeintel=not args.no_codeintel)
        else:
            graph = build_code_graph(root, use_codeintel=not args.no_codeintel)
    except (WorkspaceError, GraphError, OSError) as exc:
        raise CliError(str(exc)) from exc
    if args.knowledge_root:
        graph = graph.merge(knowledge_graph(args.knowledge_root))
    out = Path(args.out) if args.out else default_state_dir(root) / "graph.json"
    fingerprint = save_graph(graph, out)
    return {
        "status": "ok",
        "path": out.as_posix(),
        "fingerprint": fingerprint,
        "stats": graph.stats(),
        "unresolved": graph.unresolved[: args.limit],
        "incremental": {k: v for k, v in report.items() if k in ("rebuilt", "reused", "removed")},
    }


def _query(args: argparse.Namespace) -> dict[str, Any]:
    graph = _load(args.graph)
    if args.neighbors:
        try:
            items = neighbors(graph, args.neighbors, relation=args.relation,
                              direction=args.direction)
        except GraphError as exc:
            raise CliError(str(exc)) from exc
        return {"status": "ok", "node": args.neighbors, "neighbors": items[: args.limit],
                "total": len(items)}
    if args.path:
        path = shortest_path(graph, args.path[0], args.path[1], max_depth=args.depth)
        return {"status": "ok" if path else "unresolved", "path": path}
    nodes = find_nodes(graph, kind=args.kind, layer=args.layer)
    return {"status": "ok", "nodes": [n.to_dict() for n in nodes[: args.limit]],
            "total": len(nodes)}


def _impact(args: argparse.Namespace) -> dict[str, Any]:
    graph = _load(args.graph)
    result = impact(graph, args.changed, max_depth=args.depth)
    result["status"] = "ok" if result["changed"] else "unresolved"
    return result


def _federate(args: argparse.Namespace) -> dict[str, Any]:
    static = _load(args.static) if args.static else None
    live = _load(args.live) if args.live else None
    artifact = _load(args.artifact) if args.artifact else None
    knowledge = knowledge_graph(args.knowledge_root) if args.knowledge_root else None
    if not any((static, live, artifact, knowledge)):
        raise CliError("federate needs at least one of --static/--live/--artifact/--knowledge-root")
    result = federate(static, live, artifact, knowledge)
    out: dict[str, Any] = {
        "status": "ok",
        "sources": result.sources,
        "stats": result.graph.stats(),
        "ambiguous_names": result.ambiguous_names,
        "unresolved": result.unresolved[: args.limit],
    }
    if args.out:
        out["path"] = Path(args.out).as_posix()
        out["fingerprint"] = save_graph(result.graph, args.out)
    return out


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("graph", help="Graphfy: semantic/workspace graph (offline)")
    s = p.add_subparsers(dest="graph_cmd", metavar="<op>")

    b = s.add_parser("build", help="build the static workspace/code graph")
    b.add_argument("--root", required=True, help="workspace or repository root")
    b.add_argument("--manifest", help=f"workspace manifest (default <root>/{MANIFEST_NAME})")
    b.add_argument("--out", help="graph JSON output (default .sparkforge-azure/graph/graph.json)")
    b.add_argument("--knowledge-root", help="merge knowledge/skills/agents from this root")
    b.add_argument("--no-codeintel", action="store_true", help="force the ast fallback")
    b.add_argument("--limit", type=int, default=50)
    b.set_defaults(func=_build)

    q = s.add_parser("query", help="query a graph by kind/layer, neighbors or path")
    q.add_argument("--graph", required=True)
    mode = q.add_mutually_exclusive_group(required=True)
    mode.add_argument("--kind")
    mode.add_argument("--layer")
    mode.add_argument("--neighbors", metavar="NODE_ID")
    mode.add_argument("--path", nargs=2, metavar=("FROM", "TO"))
    q.add_argument("--relation")
    q.add_argument("--direction", choices=("out", "in", "both"), default="out")
    q.add_argument("--depth", type=int, default=6)
    q.add_argument("--limit", type=int, default=100)
    q.set_defaults(func=_query)

    i = s.add_parser("impact", help="change impact of files/symbols/knowledge ids")
    i.add_argument("--graph", required=True)
    i.add_argument("--changed", nargs="+", required=True, help="path, node id or knowledge id")
    i.add_argument("--depth", type=int, default=3)
    i.set_defaults(func=_impact)

    f = s.add_parser("federate", help="compose static+live+artifact+knowledge by explicit ids")
    f.add_argument("--static")
    f.add_argument("--live")
    f.add_argument("--artifact")
    f.add_argument("--knowledge-root")
    f.add_argument("--out")
    f.add_argument("--limit", type=int, default=100)
    f.set_defaults(func=_federate)

    v = s.add_parser("view", help="emit the ForgeGraphView/v1 document (Graph Studio)")
    v.add_argument(
        "--graph",
        help="saved graph JSON (default: .sparkforge-azure/graph/graph.json)",
    )
    v.set_defaults(func=_view)

    u = s.add_parser("ui", help="open the local Graph Studio explorer for a graph")
    u.add_argument(
        "--graph",
        help="saved graph JSON (default: .sparkforge-azure/graph/graph.json)",
    )
    u.add_argument(
        "--no-browser", action="store_true",
        help="serve without opening a browser (SSH)")
    u.add_argument("--port", type=int, default=0, help="port to bind (default ephemeral)")
    u.set_defaults(func=_ui)


def _graph_path(args: argparse.Namespace) -> Path:
    if args.graph:
        return Path(args.graph)
    from sparkforge_azure.graph.store import default_state_dir

    return default_state_dir(Path.cwd()) / "graph.json"


def _no_graph_refusal(path: Path) -> dict[str, Any]:
    # forge-protocol refusal envelope: federation (`theforge graph
    # --federated`) names the code; `status: refused` keeps the nonzero
    # exit and the human message on `detail`
    return {
        "refusal": "SFA-GRAPH-NO-GRAPH",
        "status": "refused",
        "detail": f"no readable graph at {path} — run `graph build` first",
        "unlock": "sparkforge-azure graph build --root <repo>",
    }


def _view(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.graphview import build_view

    path = _graph_path(args)
    view = build_view(path)
    if view is None:
        return _no_graph_refusal(path)
    return view.to_dict()


def _ui(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure._graphstudio import graph_studio_enabled, open_studio
    from sparkforge_azure.graphview import build_view

    if not graph_studio_enabled(
        Path.cwd(),
        state_rel=".sparkforge-azure",
        user_state_rel="~/.sparkforge-azure",
    ):
        return {
            "refusal": "SFA-GRAPH-STUDIO-DISABLED",
            "status": "refused",
            "detail": "Graph Studio declined at install "
            "(components.json: graph_studio=false)",
            "unlock": "reinstall with the graph-studio component",
        }
    path = _graph_path(args)
    view = build_view(path)
    if view is None:
        return _no_graph_refusal(path)
    rc = open_studio([view], open_browser=not args.no_browser, port=args.port)
    return {"status": "completed" if rc == 0 else "failed", "served": rc == 0}
