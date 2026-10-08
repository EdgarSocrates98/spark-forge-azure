"""``sparkforge-azure diagnose`` -- offline diagnosis on a case bundle.

Two verticals share the verb:
  * ``diagnose --bundle|--suite``        — Databricks UC/ADLS access (default)
  * ``diagnose fabric --bundle|--suite`` — Microsoft Fabric (Lakehouse,
    OneLake security, shortcuts, Spark, capacity, Data Factory seam)
"""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.azure.casefile import CaseError as AccessCaseError
from sparkforge_azure.azure.pipeline import run_case
from sparkforge_azure.azure.suite import run_suite
from sparkforge_azure.cli import CliError
from sparkforge_azure.fabric.casefile import CaseError as FabricCaseError
from sparkforge_azure.fabric.pipeline import run_fabric_case
from sparkforge_azure.fabric.suite import run_fabric_suite


def _diagnose(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.suite:
            return run_suite(args.suite, profile=args.profile)
        if not args.bundle:
            raise CliError("diagnose requires --bundle <dir> or --suite <dir>")
        return run_case(args.bundle, profile=args.profile)
    except AccessCaseError as exc:
        raise CliError(str(exc)) from exc


def _diagnose_fabric(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.suite:
            return run_fabric_suite(args.suite, profile=args.profile)
        if not args.bundle:
            raise CliError(
                "diagnose fabric requires --bundle <dir> or --suite <dir>")
        return run_fabric_case(args.bundle, profile=args.profile)
    except FabricCaseError as exc:
        raise CliError(str(exc)) from exc


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "diagnose",
        help="offline access diagnosis on a case bundle",
    )
    inner = p.add_subparsers(dest="diagnose_domain")
    fp = inner.add_parser(
        "fabric",
        help="Microsoft Fabric vertical: workspace/OneLake/shortcut/Spark/"
             "capacity/pipeline diagnosis",
    )
    g = fp.add_mutually_exclusive_group(required=True)
    g.add_argument("--bundle",
                   help="Fabric case bundle directory (case.yaml + artifacts)")
    g.add_argument("--suite",
                   help="directory of Fabric case bundles; checks expect:")
    fp.add_argument("--profile", choices=("economy", "balanced", "deep"),
                    default="balanced")
    fp.set_defaults(func=_diagnose_fabric)

    g = p.add_mutually_exclusive_group()
    g.add_argument("--bundle",
                   help="case bundle directory (case.yaml + artifacts)")
    g.add_argument("--suite",
                   help="directory of case bundles; checks each expect: block")
    p.add_argument("--profile", choices=("economy", "balanced", "deep"),
                   default="balanced")
    p.set_defaults(func=_diagnose)
