"""``sparkforge-azure offline-bundle build|verify``."""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.bundle import BundleError, build_bundle, verify_bundle
from sparkforge_azure.cli.main import CliError
from sparkforge_azure.doctor import data_root


def _build(a: argparse.Namespace) -> dict[str, Any]:
    try:
        return build_bundle(
            a.out, facts=a.facts, findings=a.findings, graph=a.graph,
            graph_seeds=a.seed or (), receipts=a.receipt or (), config=a.config,
            knowledge_root=data_root("knowledge"), knowledge_ids=a.knowledge or (),
            catalog_dir=data_root("rules") / "catalog",
            matrices_dir=data_root("knowledge") / "matrices",
        )
    except (BundleError, OSError, ValueError) as exc:
        raise CliError(str(exc)) from exc


def _verify(a: argparse.Namespace) -> dict[str, Any]:
    return verify_bundle(a.path)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("offline-bundle", help="redacted evidence bundle (no secrets, no raw dumps)")
    s = p.add_subparsers(dest="bundle_cmd", metavar="<op>")
    b = s.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--facts")
    b.add_argument("--findings")
    b.add_argument("--graph")
    b.add_argument("--seed", action="append", help="graph node id to slice around")
    b.add_argument("--receipt", action="append")
    b.add_argument("--config")
    b.add_argument("--knowledge", action="append", help="extra knowledge id")
    b.set_defaults(func=_build)
    v = s.add_parser("verify")
    v.add_argument("path")
    v.set_defaults(func=_verify)
