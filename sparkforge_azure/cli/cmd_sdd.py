"""``sparkforge-azure sdd`` -- spec-driven development gate.

  * ``sdd check [--feature F]``  — validate SDD artifact chain
    (define -> design -> plan -> build_report); refused entries exit 1
  * ``sdd status``               — phase/status of every feature spec

The gate is `sparkforge_azure.sdd.checks.check`; this command is the
documented surface for it (AGENTS.md/CONTRIBUTING.md).
"""
from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.sdd.checks import check as sdd_check
from sparkforge_azure.sdd.status import status as sdd_status


def _check(args: argparse.Namespace) -> dict[str, Any]:
    out = sdd_check(".", feature=args.feature)
    out["status"] = "ok" if out.get("ok") else "fail"
    return out


def _status(args: argparse.Namespace) -> dict[str, Any]:
    out = sdd_status(".")
    out["status"] = "ok"
    return out


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "sdd",
        help="SDD gate — spec artifact chain check/status",
    )
    inner = p.add_subparsers(dest="sdd_op")

    cp = inner.add_parser(
        "check", help="validate the SDD artifact chain (all features or --feature)")
    cp.add_argument("--feature", help="check a single feature (dir name)")
    cp.set_defaults(func=_check)

    sp = inner.add_parser(
        "status", help="phase/status of every feature under docs/sdd")
    sp.set_defaults(func=_status)
