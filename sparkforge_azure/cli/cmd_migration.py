"""``sparkforge-azure migration`` -- ADF/Synapse -> Fabric assessment.

  * ``migration inventory --bundle``  — estate summary + readiness census
  * ``migration assess --bundle|--suite`` — full assessment report
  * ``migration plan --bundle``       — readiness + waves + rollback
  * ``migration validate --bundle``   — post-migration validation dims

All offline; JSON-only contract (prompt §242-243).
"""
from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.cli import CliError
from sparkforge_azure.migration.casefile import MigrationCaseError
from sparkforge_azure.migration.pipeline import run_migration_case
from sparkforge_azure.migration.suite import run_migration_suite


def _run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return run_migration_case(args.bundle, profile=args.profile)
    except MigrationCaseError as exc:
        raise CliError(str(exc)) from exc


def _inventory(args: argparse.Namespace) -> dict[str, Any]:
    r = _run(args)
    return {"status": r["status"], "estate": r["estate"],
            "readiness": r["readiness"], "unresolved": r["unresolved"],
            "receipt": r["receipt"]}


def _assess(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.suite:
            return run_migration_suite(args.suite, profile=args.profile)
    except MigrationCaseError as exc:
        raise CliError(str(exc)) from exc
    if not args.bundle:
        raise CliError(
            "migration assess requires --bundle <dir> or --suite <dir>")
    return _run(args)


def _plan(args: argparse.Namespace) -> dict[str, Any]:
    r = _run(args)
    return {"status": r["status"], "readiness": r["readiness"],
            "plan": r["plan"], "upstream_blockers": r["upstream_blockers"],
            "conflicts": r["conflicts"], "receipt": r["receipt"]}


def _validate(args: argparse.Namespace) -> dict[str, Any]:
    r = _run(args)
    if r["validation"] is None:
        return {"status": "unresolved",
                "reason": "bundle has no validation.json",
                "receipt": r["receipt"]}
    return {"status": r["validation"]["overall"],
            "validation": r["validation"], "receipt": r["receipt"]}


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "migration",
        help="ADF/Synapse -> Fabric migration assessment (offline)",
    )
    inner = p.add_subparsers(dest="migration_op")

    def _bundle_or_suite(sp: argparse.ArgumentParser, suite: bool) -> None:
        g = sp.add_mutually_exclusive_group(required=True)
        g.add_argument("--bundle",
                       help="migration case bundle directory")
        if suite:
            g.add_argument("--suite",
                           help="directory of migration case bundles")
        sp.add_argument("--profile",
                        choices=("economy", "balanced", "deep"),
                        default="balanced")

    ip = inner.add_parser(
        "inventory", help="estate summary + readiness census")
    _bundle_or_suite(ip, suite=False)
    ip.set_defaults(func=_inventory)

    ap = inner.add_parser(
        "assess", help="full assessment (readiness+recs+waves+validation)")
    _bundle_or_suite(ap, suite=True)
    ap.set_defaults(func=_assess)

    pp = inner.add_parser(
        "plan", help="migration waves + rollback + upstream blockers")
    _bundle_or_suite(pp, suite=False)
    pp.set_defaults(func=_plan)

    vp = inner.add_parser(
        "validate", help="post-migration validation dimensions")
    _bundle_or_suite(vp, suite=False)
    vp.set_defaults(func=_validate)
