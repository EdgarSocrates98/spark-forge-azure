"""Core commands: ``version``."""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure import __version__


def _version(_: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": "ok",
        "engine": "spark-forge-azure",
        "cli": "sparkforge-azure",
        "version": __version__,
        "provider": "azure",
        "domain": "data",
    }


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("version", help="print engine identity and version")
    p.set_defaults(func=_version)
