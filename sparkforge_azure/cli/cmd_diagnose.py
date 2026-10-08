"""``sparkforge-azure diagnose`` -- offline access diagnosis on a case bundle."""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.azure.casefile import CaseError
from sparkforge_azure.azure.pipeline import run_case
from sparkforge_azure.azure.suite import run_suite
from sparkforge_azure.cli import CliError


def _diagnose(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.suite:
            return run_suite(args.suite, profile=args.profile)
        if not args.bundle:
            raise CliError("diagnose requires --bundle <dir> or --suite <dir>")
        return run_case(args.bundle, profile=args.profile)
    except CaseError as exc:
        raise CliError(str(exc)) from exc


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "diagnose",
        help="offline UC/RBAC/ACL/network access diagnosis on a case bundle",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--bundle",
                   help="case bundle directory (case.yaml + artifacts)")
    g.add_argument("--suite",
                   help="directory of case bundles; checks each expect: block")
    p.add_argument("--profile", choices=("economy", "balanced", "deep"),
                   default="balanced")
    p.set_defaults(func=_diagnose)
