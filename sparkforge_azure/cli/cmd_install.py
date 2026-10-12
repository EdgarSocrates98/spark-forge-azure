"""``sparkforge-azure install`` — forge/* governed lifecycle surface.

Bare ``install`` applies (writes managed assets); the optional positional
selects the read-only or mutating verb: ``status``, ``doctor``, ``repair``,
``uninstall``, ``update``, ``mcp-verify``. Same verbs as every sibling
Forge — ``theforge install auto`` delegates here.
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
        except Exception as exc:
            # Vendored installkit refusals carry the forge/* kind — translate
            # into a named refusal, never a traceback (spec §179).
            kind = getattr(exc, "kind", None)
            if isinstance(kind, str) and kind.startswith("FORGE-INSTALL"):
                return refused_document(PortableError(kind, getattr(exc, "detail", str(exc))))
            raise

    return wrapped


def _root(args: argparse.Namespace) -> Path | None:
    return Path(args.root) if args.root else None


def _tty() -> bool:
    import sys

    return sys.stdin.isatty() and sys.stdout.isatty()


def run_guided_install() -> int:
    """Run guided install through the shared wizard and real service."""
    from sparkforge_azure.install import service
    from sparkforge_azure.ui.kit import UIContext
    from sparkforge_azure.ui.wizard import run_wizard

    return run_wizard(
        forge_name="spark-forge-azure",
        install_fn=lambda **kw: service.install(root=None, **kw),
        doctor_fn=lambda **kw: service.doctor(**kw),
        ctx=UIContext.detect(),
    )


def _install(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    comps = (
        tuple(c.strip() for c in args.components.split(",") if c.strip())
        if getattr(args, "components", None)
        else None
    )
    call = lambda **kw: service.install(  # noqa: E731
        scope=args.scope,
        root=_root(args),
        host=args.host,
        profile=args.profile,
        components=comps,
        **kw,
    )
    if not args.yes and not args.dry_run and _tty():
        # Interactive approval: render the plan, confirm once, apply.
        from sparkforge_azure.ui.kit import NonInteractive, approve_plan

        plan = call(yes=False, dry_run=True)
        try:
            approved = approve_plan(plan)
        except NonInteractive:
            approved = False
        if not approved:
            return {
                "schema": "forge/InstallReceipt/v1",
                "forge_id": "spark-forge-azure",
                "operation": "install",
                "status": "declined",
                "checks": [],
                "managed_files": [],
                "verification": {"status": "UNVERIFIED"},
                "error": {"kind": "SFA-INSTALL-DECLINED", "detail": "declined — nothing written"},
            }
        return call(yes=True, dry_run=False)
    return call(yes=args.yes, dry_run=args.dry_run)


def _status(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    return service.status(scope=args.scope, root=_root(args))


def _doctor(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    return service.doctor(scope=args.scope, root=_root(args))


def _repair(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    return service.repair(scope=args.scope, root=_root(args), dry_run=args.dry_run)


def _uninstall(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    return service.uninstall(
        scope=args.scope, root=_root(args), purge=args.purge, dry_run=args.dry_run
    )


def _update(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    return service.update(
        to=args.to, repo=Path(args.repo) if args.repo else None, dry_run=args.dry_run
    )


def _mcp_verify(args: argparse.Namespace) -> dict[str, Any]:
    from sparkforge_azure.install import service

    return service.mcp_verify()


_OPS: dict[str, Callable[[argparse.Namespace], dict[str, Any]]] = {
    "apply": _install,
    "status": _status,
    "doctor": _doctor,
    "repair": _repair,
    "uninstall": _uninstall,
    "update": _update,
    "mcp-verify": _mcp_verify,
}


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    fn = _OPS.get(args.op)
    if fn is None:
        return refused_document(
            PortableError("usage", f"install op {args.op!r}; expected one of {sorted(_OPS)}")
        )
    return fn(args)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "install",
        help="forge/* install lifecycle: apply/status/doctor/repair/uninstall/update/mcp-verify",
    )
    p.add_argument(
        "op",
        nargs="?",
        default="apply",
        choices=sorted(_OPS),
        help="lifecycle verb (default: apply — writes managed assets)",
    )
    p.add_argument("--scope", choices=("project", "workspace", "user"), default="project")
    p.add_argument("--root", default=None, help="explicit target root (default: resolved from cwd)")
    p.add_argument("--host", default="all", choices=("claude", "devin", "codex", "copilot", "all"))
    p.add_argument("--profile", default="recommended", choices=("minimal", "recommended", "full"))
    p.add_argument(
        "--yes", "-y", action="store_true", help="explicit approval — required for any write"
    )
    p.add_argument(
        "--components",
        default=None,
        help="optional components csv: skills,agents,mcp,tui,graph-studio",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--purge", action="store_true", help="uninstall: also delete .sparkforge-azure state"
    )
    p.add_argument("--to", default=None, help="update: pinned version — never 'latest'")
    p.add_argument("--repo", default=None)
    p.set_defaults(func=_run(_dispatch))
