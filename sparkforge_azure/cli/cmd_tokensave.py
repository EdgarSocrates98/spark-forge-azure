"""``sparkforge-azure tokensave search|read|symbols|refs|diff|expand|context``."""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.tokensave import TokenSave


def _ts(args: argparse.Namespace) -> TokenSave:
    return TokenSave(args.root, profile_name=args.profile, index_db=args.index)


def _wrap(ts: TokenSave, result: Any) -> dict[str, Any]:
    refused = isinstance(result, dict) and result.get("refused")
    return {"status": "refused" if refused else "ok", "result": result,
            "ledger": ts.ledger.summary(), "authority": "data_only"}


def _search(a):
    ts = _ts(a)
    return _wrap(ts, ts.search(a.query, limit=a.limit))


def _read(a):
    ts = _ts(a)
    return _wrap(ts, ts.read(a.path, a.start, a.end))


def _symbols(a):
    ts = _ts(a)
    return _wrap(ts, ts.symbols(a.path))


def _refs(a):
    ts = _ts(a)
    return _wrap(ts, ts.refs(a.name))


def _diff(a):
    ts = _ts(a)
    return _wrap(ts, ts.diff(a.rev, a.path))


def _expand(a):
    ts = _ts(a)
    return _wrap(ts, ts.expand(a.node_id, depth=a.depth))


def _context(a):
    ts = _ts(a)
    res = ts.context(a.task, required_terms=a.term or None).to_dict()
    res["status"] = "ok" if res["status"] == "sufficient" else res["status"]
    return res


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("tokensave", help="economical retrieval ladder (L0-L6)")
    s = p.add_subparsers(dest="tokensave_cmd", metavar="<op>")

    def common(q: argparse.ArgumentParser) -> None:
        q.add_argument("--root", default=".")
        q.add_argument("--profile", choices=("economy", "balanced", "deep"), default="economy")
        q.add_argument("--index", default=None, help="code-intelligence index (sqlite)")

    q = s.add_parser("search", help="L1 literal search")
    common(q)
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=None)
    q.set_defaults(func=_search)
    q = s.add_parser("read", help="L5 bounded slice")
    common(q)
    q.add_argument("path")
    q.add_argument("--start", type=int, default=1)
    q.add_argument("--end", type=int, default=None)
    q.set_defaults(func=_read)
    q = s.add_parser("symbols", help="L2 symbols of a file")
    common(q)
    q.add_argument("path")
    q.set_defaults(func=_symbols)
    q = s.add_parser("refs", help="L2 references of a symbol")
    common(q)
    q.add_argument("name")
    q.set_defaults(func=_refs)
    q = s.add_parser("diff", help="bounded git diff")
    common(q)
    q.add_argument("--rev", default="HEAD")
    q.add_argument("--path", default=None)
    q.set_defaults(func=_diff)
    q = s.add_parser("expand", help="L3 graph expansion (needs --index)")
    common(q)
    q.add_argument("node_id")
    q.add_argument("--depth", type=int, default=None)
    q.set_defaults(func=_expand)
    q = s.add_parser("context", help="walk the ladder until sufficient")
    common(q)
    q.add_argument("task")
    q.add_argument("--term", action="append", help="required term (repeatable)")
    q.set_defaults(func=_context)
