"""``sparkforge-azure delegate`` — governed peer delegation (lf-0029).

Subcommands:

- ``discover`` — resolve declared specialists on this machine (PATH,
  package metadata, manifests, governed probes) → named discovery states.
- ``plan <intent>`` — deterministic routing to a declared capability,
  with refusals; executes nothing.
- ``run <provider> <capability>`` — execute one declared capability under
  the governed boundary (argv only, scrubbed env, timeout, output caps,
  risk gate). Evidence lands as a sealed ``EvidenceHandoff`` under
  ``.sparkforge-azure/delegation/handoffs/``.
- ``handoffs`` — list the persisted handoffs.

``run`` accepts capability values as flags mapped onto the declared
entrypoint placeholders (``VALUES_KEYS``); unset flags are dropped with
their ``--flag`` token, never passed through. Cloud-shaped risk levels
require an explicit ``--authorize`` grant — declared capabilities today
are all LOCAL_READ, but the gate is armed regardless (deny by default).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

RISKS = (
    "LOCAL_READ", "LOCAL_WRITE", "EXTERNAL_READ",
    "EXTERNAL_WRITE", "DESTRUCTIVE", "COST_BEARING",
)


def _workspace(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "root", None) or ".")


def _discover(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.delegation import run as delegation_run

    return delegation_run.discover(
        probe=not args.no_probe,
        workspace=_workspace(args),
        provider=args.provider,
    )


def _plan(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.delegation import run as delegation_run

    return delegation_run.plan(
        args.intent,
        authorized_risks=set(args.authorize or []),
        workspace=_workspace(args),
        probe=not args.no_probe,
    )


def _run_delegate(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.delegation import run as delegation_run

    values: dict[str, str | None] = {
        key: getattr(args, key, None) for key in delegation_run.VALUES_KEYS
    }
    return delegation_run.delegate(
        args.provider,
        args.capability,
        values=values,
        authorized_risks=set(args.authorize or []),
        timeout_s=args.timeout,
        workspace=_workspace(args),
        persist=not args.no_persist,
    )


def _handoffs(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.delegation import run as delegation_run

    return delegation_run.handoffs(workspace=_workspace(args))


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "delegate",
        help="governed delegation to optional specialists "
        "(data-sentinel, forge-doctor-data)",
    )
    leaf = p.add_subparsers(dest="delegate_op", metavar="<op>")

    d = leaf.add_parser(
        "discover",
        help="discover declared specialists: PATH, package, handshake, "
        "capability manifest",
    )
    d.add_argument(
        "--provider",
        choices=["data-sentinel-forge", "forge-doctor-data"],
        help="restrict discovery to one provider",
    )
    d.add_argument("--no-probe", action="store_true",
                   help="presence evidence only — never executes a CLI")
    d.add_argument("--root", default=".", help="workspace root (default: cwd)")
    d.set_defaults(func=_discover)

    pl = leaf.add_parser(
        "plan",
        help="deterministic delegation plan for an intent — executes nothing",
    )
    pl.add_argument("intent", help="free-text intent (routed over declared intents)")
    pl.add_argument(
        "--authorize",
        action="append",
        choices=list(RISKS),
        default=[],
        help="grant a risk level for the plan (repeatable)",
    )
    pl.add_argument("--no-probe", action="store_true")
    pl.add_argument("--root", default=".")
    pl.set_defaults(func=_plan)

    r = leaf.add_parser(
        "run",
        help="execute one declared capability under the governed boundary",
    )
    r.add_argument("provider",
                   choices=["data-sentinel-forge", "forge-doctor-data"])
    r.add_argument("capability", help="declared capability id")
    r.add_argument("--target", help="file/dir the capability analyzes")
    r.add_argument("--runtime", help="runtime label (lakehouse compat)")
    r.add_argument("--operation", help="lakehouse operation (merge|append|ddl)")
    r.add_argument("--table-format", dest="table_format",
                   help="table format (delta|iceberg)")
    r.add_argument("--check", help="doctor scan single check/category")
    r.add_argument("--dialect", help="SQL dialect (spark|trino)")
    r.add_argument("--timeout", type=float, help="seconds")
    r.add_argument("--no-persist", action="store_true",
                   help="do not persist the evidence handoff")
    r.add_argument(
        "--authorize",
        action="append",
        choices=list(RISKS),
        default=[],
        help="grant a risk level (repeatable); cloud-shaped levels "
        "never run without an explicit grant",
    )
    r.add_argument("--root", default=".")
    r.set_defaults(func=_run_delegate)

    h = leaf.add_parser(
        "handoffs",
        help="list evidence handoffs persisted under "
        ".sparkforge-azure/delegation/handoffs/",
    )
    h.add_argument("--root", default=".")
    h.set_defaults(func=_handoffs)
