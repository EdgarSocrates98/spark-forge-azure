"""``sparkforge-azure workspace`` -- ForgeWorkspace lifecycle.

A ForgeWorkspace is the logical grouping of projects the portable
distribution operates on (prompt_evo_portable.md §20–§36) — local,
declared, deterministic. ``discover`` suggests without writing;
``init``/``add``/``remove`` mutate only ``.sparkforge-azure/workspace.yaml``
(plus the target's portable identity on ``add``); ``status`` reports
resolution and dependency cycles as an explicit review state.
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


def _discover(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import workspace

    return workspace.workspace_discover(Path(args.root))


def _init(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import workspace

    return workspace.workspace_init(Path(args.root), name=args.name)


def _add(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import workspace

    return workspace.workspace_add(
        Path(args.root),
        args.path,
        project_id=args.id,
        role=args.role,
        depends_on=tuple(args.depends_on or ()),
        optional=tuple(args.optional or ()),
    )


def _remove(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import workspace

    return workspace.workspace_remove(Path(args.root), args.id)


def _status(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.distribution import workspace

    return workspace.workspace_status(Path(args.root))


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "workspace",
        help="ForgeWorkspace: discover/init/add/remove/status of declared projects",
    )
    leaf = p.add_subparsers(dest="workspace_op", metavar="<op>")

    def with_root(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--root", default=".", help="starting dir (default: cwd)")

    d = leaf.add_parser(
        "discover", help="suggest candidate projects — reads, never writes"
    )
    with_root(d)
    d.set_defaults(func=_run(_discover))

    i = leaf.add_parser("init", help="create workspace.yaml + register the host project")
    with_root(i)
    i.add_argument("--name", help="workspace name (default: directory name)")
    i.set_defaults(func=_run(_init))

    a = leaf.add_parser("add", help="declare a repository as a workspace member")
    with_root(a)
    a.add_argument("path", help="repo dir — relative to the workspace root or absolute")
    a.add_argument("--id", help="expected project_id (collision check)")
    a.add_argument(
        "--role",
        choices=["application", "data", "infra", "shared", "tests", "docs"],
        help="advisory role",
    )
    a.add_argument("--depends-on", nargs="*", metavar="ID", help="direct dependency ids")
    a.add_argument("--optional", nargs="*", metavar="ID", help="optional dependency ids")
    a.set_defaults(func=_run(_add))

    r = leaf.add_parser(
        "remove", help="drop a project declaration (the repository is never deleted)"
    )
    with_root(r)
    r.add_argument("id", help="declared project id")
    r.set_defaults(func=_run(_remove))

    s = leaf.add_parser("status", help="declared projects, resolution and cycles")
    with_root(s)
    s.set_defaults(func=_run(_status))
