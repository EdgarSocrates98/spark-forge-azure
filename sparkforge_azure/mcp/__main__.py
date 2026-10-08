"""``python -m sparkforge_azure.mcp`` -- stdio server direto (padrão MCP host).

Host MCP aponta para `python -m sparkforge_azure.mcp` em `args`. O stdout é o
canal JSON-RPC: nada aqui escreve nele além do SDK. Flags espelham
`sparkforge-azure mcp serve`.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m sparkforge_azure.mcp")
    parser.add_argument("--compact", action="store_true", help="read-only catalog only")
    parser.add_argument("--no-local-write", action="store_true")
    parser.add_argument("--cloud-read", action="store_true")
    parser.add_argument("--cloud-write-grant", metavar="TOKEN")
    args = parser.parse_args()

    import anyio

    from sparkforge_azure.mcp.dispatch import CallPolicy
    from sparkforge_azure.mcp.server import serve_stdio

    policy = CallPolicy(
        compact=args.compact,
        allow_local_write=not args.no_local_write,
        cloud_read_enabled=args.cloud_read,
        cloud_write_grant=args.cloud_write_grant,
    )
    anyio.run(serve_stdio, policy)


if __name__ == "__main__":
    main()
