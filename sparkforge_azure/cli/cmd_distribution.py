"""``sparkforge-azure distribution`` -- portable lifecycle surface.

``inspect`` answers where the package, state, cache, hosts and identities
live without mutating anything. ``init`` writes only managed metadata
(project identity, ``.mcp.json`` key, ledger, receipt) and is idempotent.
``status`` reports ``initialized|uninitialized|partial|drifted|broken`` with
per-asset drift. ``doctor`` is offline diagnostics; ``detach`` (W6) removes
only managed assets. Every refusal is a structured ``error.kind``
(prompt_evo_portable.md §177–§180) — never a traceback.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sparkforge_azure.distribution.errors import PortableError, refused_document


def _run(fn: Callable[[argparse.Namespace], dict[str, Any]]) -> Callable:
    def wrapped(args: argparse.Namespace) -> dict[str, Any]:
        try:
            return fn(args)
        except PortableError as exc:
            return refused_document(exc)

    return wrapped


def _inspect(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import service

    return service.inspect(Path(args.root))


def _init(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import service

    return service.initialize(
        Path(args.root), name=args.name, regen_id=args.regen_id
    )


def _status(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import service

    return service.status(Path(args.root))


def _doctor(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import service

    return service.doctor(Path(args.root))


def _detach(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import detach as detach_service

    return detach_service.detach(
        Path(args.root),
        dry_run=args.dry_run,
        purge_state=args.purge_state,
        purge_cache=args.purge_cache,
    )


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "distribution",
        help="portable distribution lifecycle: inspect/init/status/doctor/detach",
    )
    leaf = p.add_subparsers(dest="distribution_op", metavar="<op>")

    def with_root(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--root", default=".", help="project root (default: cwd)")

    i = leaf.add_parser("inspect", help="show resolved paths, assets, hosts and identities")
    with_root(i)
    i.set_defaults(func=_run(_inspect))

    n = leaf.add_parser("init", help="initialize portable identity + local integration")
    with_root(n)
    n.add_argument("--name", help="project name (default: directory name)")
    n.add_argument(
        "--regen-id",
        action="store_true",
        help="mint a new project_id (for a copied/cloned project)",
    )
    n.set_defaults(func=_run(_init))

    s = leaf.add_parser("status", help="initialization state + managed-asset drift")
    with_root(s)
    s.set_defaults(func=_run(_status))

    d = leaf.add_parser("doctor", help="offline portable health (no Azure auth)")
    with_root(d)
    d.set_defaults(func=_run(_doctor))

    t = leaf.add_parser("detach", help="remove managed integration assets (reversible)")
    with_root(t)
    t.add_argument("--dry-run", action="store_true", help="report what would be removed")
    t.add_argument(
        "--purge-state", action="store_true", help="also remove .sparkforge-azure state"
    )
    t.add_argument(
        "--purge-cache", action="store_true", help="also remove the managed cache dir"
    )
    t.set_defaults(func=_run(_detach))
