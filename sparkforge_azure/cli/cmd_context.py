"""``sparkforge-azure context resolve`` -- workspace-scoped context.

Resolves *which projects* the declared dependency graph allows for a target
(§64) and, with ``--task``, runs the TokenSave L0→L6 ladder per project —
each engine confined to its own root, never reading a sibling's files.
Emits the §58 receipt (considered/selected, files, bytes, stop_reason) and
persists it to ``receipt-context.json``.
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


def _resolve(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution.context import context_resolve

    return context_resolve(
        Path(args.root),
        target=args.target,
        scope=args.scope,
        task=args.task or "",
        profile=args.profile,
    )


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "context",
        help="workspace-scoped context resolution (target|direct|transitive|all)",
    )
    leaf = p.add_subparsers(dest="context_op", metavar="<op>")

    r = leaf.add_parser(
        "resolve",
        help="resolve the relevant project set + bounded context pack for a target",
    )
    r.add_argument("--root", default=".", help="starting dir (default: cwd)")
    r.add_argument(
        "--target",
        help="project id or path (default: workspace default_target)",
    )
    r.add_argument(
        "--scope",
        choices=["target", "direct", "transitive", "all"],
        default="target",
        help="locality scope (default: target — never the whole workspace by omission)",
    )
    r.add_argument(
        "--profile",
        choices=["economy", "balanced", "deep"],
        default="economy",
        help="TokenSave budget profile (default: economy)",
    )
    r.add_argument(
        "--task",
        help="task text — engages the per-project L0→L6 ladder (default: project set only)",
    )
    r.set_defaults(func=_run(_resolve))
