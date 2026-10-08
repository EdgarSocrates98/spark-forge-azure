"""``sparkforge-azure mcp ...`` -- operação do servidor MCP real.

``mcp catalog`` emite o catálogo `sfa_*` como JSON (inspeção offline).
``mcp serve`` sobe o server oficial do SDK: com ``--transport stdio`` o
stdout passa a ser o canal do protocolo JSON-RPC — o documento JSON do
contrato CLI só sai depois que a sessão termina (o client controla a vida).
Sem o extra ``mcp`` instalado o comando recusa com CliError (exit 2), nunca
ImportError cru.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from sparkforge_azure.cli.main import CliError


def _load_dispatch() -> Any:
    try:
        from sparkforge_azure.mcp import dispatch, server
    except ImportError as exc:
        raise CliError(
            "MCP runtime unavailable: install with `pip install sparkforge-azure[mcp]` "
            f"(missing: {exc.name})"
        ) from exc
    return dispatch, server


def _catalog(args: argparse.Namespace) -> dict[str, Any]:
    dispatch, _server = _load_dispatch()
    decls = dispatch.list_tools(compact=args.compact)
    return {
        "status": "ok",
        "server": _server.SERVER_NAME,
        "version": _server.server_version(),
        "compact": args.compact,
        "tools": decls,
        "tool_count": len(decls),
    }


def _policy(args: argparse.Namespace) -> Any:
    dispatch, _server = _load_dispatch()
    return dispatch.CallPolicy(
        compact=args.compact,
        allow_local_write=not args.no_local_write,
        cloud_read_enabled=args.cloud_read,
        cloud_write_grant=args.cloud_write_grant,
        # sob http o default muda: um endpoint de rede não vaza fonte do
        # workspace a menos que o operador peça explicitamente.
        allow_source_tools=(
            args.allow_source_tools or getattr(args, "transport", "stdio") == "stdio"
        ),
    )


def _serve(args: argparse.Namespace) -> dict[str, Any]:
    _dispatch, server = _load_dispatch()
    policy = _policy(args)
    if args.transport == "http":
        try:
            import uvicorn
        except ImportError as exc:
            raise CliError(
                "http transport requires uvicorn: `pip install uvicorn`"
            ) from exc
        app = server.serve_http(policy, host=args.host, port=args.port)
        sys.stderr.write(
            json.dumps(
                {
                    "status": "serving",
                    "transport": "http",
                    "endpoint": f"http://{args.host}:{args.port}/mcp",
                }
            )
            + "\n"
        )
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
        return {"status": "ok", "transport": "http", "server": server.SERVER_NAME}

    import anyio

    sys.stderr.write(
        json.dumps({"status": "serving", "transport": "stdio", "server": server.SERVER_NAME})
        + "\n"
    )
    anyio.run(server.serve_stdio, policy)
    return {"status": "ok", "transport": "stdio", "server": server.SERVER_NAME}


def register(sub: argparse._SubParsersAction) -> None:
    mcp = sub.add_parser("mcp", help="MCP runtime: catalog inspection and server")
    leaf = mcp.add_subparsers(dest="mcp_command", metavar="<mcp-command>")

    cat = leaf.add_parser("catalog", help="print the sfa_* tool catalog as JSON (offline)")
    cat.add_argument("--compact", action="store_true", help="read-only tools only")
    cat.set_defaults(func=_catalog)

    srv = leaf.add_parser("serve", help="run the MCP server (stdio or streamable http)")
    srv.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="stdio is the default MCP transport",
    )
    srv.add_argument("--compact", action="store_true", help="expose read-only catalog only")
    srv.add_argument(
        "--no-local-write",
        action="store_true",
        help="deny tools declared local_write",
    )
    srv.add_argument(
        "--cloud-read",
        action="store_true",
        help="allow tools declared cloud_read (default: denied)",
    )
    srv.add_argument(
        "--cloud-write-grant",
        metavar="TOKEN",
        help="explicit human grant for cloud_write tools (value is not logged)",
    )
    srv.add_argument(
        "--allow-source-tools",
        action="store_true",
        help="under --transport http, re-enable tools that return workspace source",
    )
    srv.add_argument("--host", default="127.0.0.1", help="http bind host")
    srv.add_argument("--port", type=int, default=8765, help="http bind port")
    srv.set_defaults(func=_serve)
