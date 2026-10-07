"""``sparkforge-azure lab <op>`` — Forge Lab offline (sections 169-170).

O dispatch vive em ``sparkforge_azure.lab.cli``; aqui so argparse + a ponte de
erros de contrato para ``CliError`` (exit 2). Mutacao de host (`up/down/shell/
gc`, `run --execute`) exige ``--execute --confirm`` — o guard e do lab, nao
desta camada.
"""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.cli.main import CliError
from sparkforge_azure.lab.cli import dispatch
from sparkforge_azure.lab.contract import LabContractError


def _call(a: argparse.Namespace) -> dict[str, Any]:
    try:
        result = dispatch(a)
    except (LabContractError, OSError, ValueError, KeyError) as exc:
        raise CliError(str(exc)) from exc
    # `lab verify` reports `valid`; the CLI exit contract needs `status`.
    if "valid" in result:
        result["status"] = "pass" if result["valid"] else "fail"
    # Lab statuses (`planned`, `declared_comparison`, `unresolved`, ...) are
    # not CLI statuses. `planned` is a completed op (it promised a plan);
    # `unresolved*` is an honest non-completion -> exit 1.
    lab_status = result.get("status")
    if lab_status in {"planned", "declared_comparison"}:
        result["lab_status"] = lab_status
        result["status"] = "ok"
    return result


def _lifecycle_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--project", default="sparkforge-azure-lab")
    p.add_argument("--profile")
    p.add_argument("--service")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--confirm", action="store_true")
    return p


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "lab", help="Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle"
    )
    p.add_argument("--repo", default=".", help="repository root (default .)")
    s = p.add_subparsers(dest="lab_action", metavar="<op>")
    s.required = True

    for op in ("doctor", "profiles", "verify", "scenarios"):
        s.add_parser(op).set_defaults(func=_call)

    for op in ("describe", "plan", "run"):
        q = s.add_parser(op)
        q.add_argument("scenario", nargs="?", help="scenario id (omit com --all)")
        q.add_argument("--all", action="store_true", help="todos os cenarios (plan/run)")
        q.add_argument("--backend", default="compose", choices=("compose", "testcontainers"))
        q.add_argument("--execute", action="store_true")
        q.add_argument("--confirm", action="store_true")
        q.set_defaults(func=_call)

    for op in ("inspect", "analyze"):
        q = s.add_parser(op)
        q.add_argument("path")
        q.set_defaults(func=_call)

    q = s.add_parser("compare")
    q.add_argument("--before", required=True)
    q.add_argument("--after", required=True)
    q.set_defaults(func=_call)

    q = s.add_parser("promote-fixture")
    q.add_argument("--run", required=True)
    q.add_argument("--destination", required=True)
    q.add_argument("--reviewed", action="store_true")
    q.set_defaults(func=_call)

    q = s.add_parser("reproduce")
    q.add_argument("--receipt", required=True)
    q.set_defaults(func=_call)

    for op in ("up", "down", "shell", "gc"):
        _lifecycle_flags(s.add_parser(op)).set_defaults(func=_call)
