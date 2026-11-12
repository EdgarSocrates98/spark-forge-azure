"""``sparkforge-azure obsidian`` — shared authorized-vault verbs.

Wraps the vendored ``sparkforge_azure._forge_obsidian`` engine in the
Azure CLI convention: every leaf returns a ``Result`` dict that ``_emit``
renders under the global ``--format`` flag, and named failures (missing
vault, refusals, conflicts) come back as ``status: refused`` payloads —
never tracebacks.
"""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure._forge_obsidian.cli import verb_payload

FORGE_ID = "spark-forge-azure"


def _result(payload: dict[str, Any]) -> dict[str, Any]:
    status = "ok"
    if payload.get("state") in {"refused", "failed"} or str(payload.get("code", "")).startswith(
        "OBSIDIAN-"
    ):
        status = "refused"
    return {"status": status, "obsidian": payload}


def _mk(verb: str):
    def _run(args: argparse.Namespace) -> dict[str, Any]:
        kw = {
            k: v
            for k, v in vars(args).items()
            if k not in {"command", "obsidian_command", "func", "format"}
        }
        return _result(verb_payload(FORGE_ID, verb, **kw))

    return _run


def register(sub: argparse._SubParsersAction) -> None:
    top = sub.add_parser("obsidian", help="Authorized Obsidian vault operations")
    leaves = top.add_subparsers(dest="obsidian_command", required=True)

    p = leaves.add_parser("status", help="Report configured/detected vault state")
    p.set_defaults(func=_mk("status"))

    p = leaves.add_parser("scan", help="List Markdown paths without reading bodies")
    p.add_argument("--prefix", default="")
    p.add_argument("--limit", type=int, default=200)
    p.set_defaults(func=_mk("scan"))

    p = leaves.add_parser("preview", help="Metadata + projection, never the body")
    p.add_argument("path")
    p.set_defaults(func=_mk("preview"))

    p = leaves.add_parser("sync-plan", help="Dry-run a sync of FILE into PATH")
    p.add_argument("path")
    p.add_argument("file")
    p.add_argument("--baseline-hash", dest="baseline_hash", default=None)
    p.add_argument("--classification", default="internal")
    p.set_defaults(func=_mk("sync-plan"))

    p = leaves.add_parser("export", help="Apply a reviewed sync plan")
    p.add_argument("path")
    p.add_argument("file")
    p.add_argument("--baseline-hash", dest="baseline_hash", default=None)
    p.add_argument("--classification", default="internal")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--no-moc", dest="moc", action="store_false", default=True)
    p.set_defaults(func=_mk("export"))

    p = leaves.add_parser("export-note", help="Export FILE as forges/spark-forge-azure/<name>.md")
    p.add_argument("name")
    p.add_argument("file")
    p.add_argument("--baseline-hash", dest="baseline_hash", default=None)
    p.add_argument("--classification", default="internal")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--no-moc", dest="moc", action="store_false", default=True)
    p.set_defaults(func=_mk("export-note"))

    p = leaves.add_parser("history", help="List Forge sync receipts (body-free)")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=_mk("history"))
