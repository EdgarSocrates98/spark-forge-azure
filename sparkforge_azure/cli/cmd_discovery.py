"""§6.2 discovery commands: ``capabilities``, ``rules``, ``knowledge``.

Offline, deterministic, JSON-only — the verbs that the installed
``forge/context/v1`` manifest points at via ``discovery.ops``/``commands``.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from typing import Any

from sparkforge_azure import discovery
from sparkforge_azure.cli import CliError


def _run(fn: Callable[[argparse.Namespace], dict[str, Any]]) -> Callable:
    def wrapped(args: argparse.Namespace) -> dict[str, Any]:
        try:
            return fn(args)
        except discovery.DiscoveryError as exc:
            raise CliError(f"DISCOVERY-REFUSED: {exc}") from exc
        except discovery.KnowledgeError as exc:
            raise CliError(f"KNOWLEDGE-UNAVAILABLE: {exc}") from exc

    return wrapped


def _capabilities(_: argparse.Namespace) -> dict[str, Any]:
    return discovery.capabilities()


def _rules_search(args: argparse.Namespace) -> dict[str, Any]:
    return discovery.rules_search(
        query=args.query,
        rule_id=args.id,
        category=args.category,
        severity=args.severity,
        limit=args.limit,
        cursor=args.cursor,
        index=args.index,
    )


def _rules_get(args: argparse.Namespace) -> dict[str, Any]:
    return discovery.rules_get(args.rule_id)


def _knowledge_search(args: argparse.Namespace) -> dict[str, Any]:
    return discovery.knowledge_search(
        args.term, domain=args.domain, limit=args.limit, cursor=args.cursor
    )


def _knowledge_get(args: argparse.Namespace) -> dict[str, Any]:
    return discovery.knowledge_get(args.file)


def _knowledge_list(args: argparse.Namespace) -> dict[str, Any]:
    return discovery.knowledge_list(limit=args.limit, cursor=args.cursor)


def register_knowledge_leaves(ks: argparse._SubParsersAction) -> None:
    """`knowledge` （cmd_analyze）：§6.2  search/get/list
    ， discovery_ops 。"""
    s = ks.add_parser("search", help="offline text search — one hit per doc (§6.2)")
    s.add_argument("term")
    s.add_argument("--domain")
    s.add_argument("--limit", type=int)
    s.add_argument("--cursor")
    s.set_defaults(func=_run(_knowledge_search))
    g = ks.add_parser("get", help="resolve one document with sha256 (§6.2)")
    g.add_argument("file")
    g.set_defaults(func=_run(_knowledge_get))
    lst = ks.add_parser("list", help="list knowledge documents")
    lst.add_argument("--limit", type=int)
    lst.add_argument("--cursor")
    lst.set_defaults(func=_run(_knowledge_list))


def context_pack(args: argparse.Namespace) -> dict[str, Any]:
    """Folha `context pack` registrada por `cmd_context`."""
    return discovery.context_pack(
        getattr(args, "domain", None),
        rules_limit=getattr(args, "rules_limit", None),
        knowledge_limit=getattr(args, "knowledge_limit", None),
        as_of=getattr(args, "as_of", None),
    )


def register(sub: argparse._SubParsersAction) -> None:
    caps = sub.add_parser(
        "capabilities",
        help="installed capabilities, protocols and the §6.2 op map (offline)",
    )
    caps.set_defaults(func=_run(_capabilities))

    rules = sub.add_parser("rules", help="rules catalog retrieval (search|get)")
    rleaf = rules.add_subparsers(dest="rules_op", metavar="<op>")
    rs = rleaf.add_parser("search", help="filter the catalog — offline, paginated")
    rs.add_argument("--query")
    rs.add_argument("--id")
    rs.add_argument("--category")
    rs.add_argument("--severity", choices=discovery.SEVERITIES)
    rs.add_argument("--limit", type=int)
    rs.add_argument("--cursor")
    rs.add_argument("--index", action="store_true", help="index fields only")
    rs.set_defaults(func=_run(_rules_search))
    rg = rleaf.add_parser("get", help="one rule by id")
    rg.add_argument("rule_id")
    rg.set_defaults(func=_run(_rules_get))
