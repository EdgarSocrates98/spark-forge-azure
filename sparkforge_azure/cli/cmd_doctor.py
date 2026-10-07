"""``sparkforge-azure doctor [--area A ...]`` -- inspection only."""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure import doctor


def _doctor(args: argparse.Namespace) -> dict[str, Any]:
    return doctor.run(args.area or None)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("doctor", help="installation and capability health (no cloud access)")
    p.add_argument("--area", action="append", help="limit to an area (repeatable)")
    p.set_defaults(func=_doctor)
