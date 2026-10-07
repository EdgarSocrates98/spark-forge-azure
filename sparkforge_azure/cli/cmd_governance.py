"""``sparkforge-azure governance diagnose --scenario <file>``."""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.azure.governance import ScenarioError, diagnose_file
from sparkforge_azure.cli.main import CliError


def _diagnose(args: argparse.Namespace) -> dict[str, Any]:
    try:
        d = diagnose_file(args.scenario)
    except (OSError, ScenarioError, ValueError) as exc:
        raise CliError(str(exc)) from exc
    out = d.to_dict()
    # exit 0 only when access is allowed; denied/unresolved are results, not errors
    out["status"] = "ok" if d.status == "allowed" else d.status
    out["access"] = d.status
    return out


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("governance", help="multi-layer governance (Entra/RBAC/ACL/UC/network)")
    s = p.add_subparsers(dest="governance_cmd", metavar="<op>")
    q = s.add_parser("diagnose", help="diagnose an access scenario offline")
    q.add_argument("--scenario", required=True, help="scenario JSON/YAML")
    q.set_defaults(func=_diagnose)
