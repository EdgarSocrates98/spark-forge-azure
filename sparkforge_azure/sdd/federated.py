"""Federated SDD adapters — sparkforge_azure → forge/* contracts (Onda 5C).

Converts native SDD artifacts into the versioned federated shapes declared
in ``the-forge/docs/portable-installation/schemas/``. Additive only: the
native engine is untouched; absence is reported, never invented.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

#: Azure uses the same phase names as AWS sibling (explore → ship).
PHASE_MAP = {
    "explore": "explore",
    "define": "define",
    "design": "design",
    "plan": "plan",
    "build_report": "build_report",
    "ship": "ship",
    "verify": "verify",
    "learn": "learn",
}

_PHASES = tuple(PHASE_MAP.values())


def map_phase(native: str) -> str:
    return PHASE_MAP.get(native, native if native in _PHASES else native)


def _item(raw: dict[str, Any], feature: str) -> dict[str, Any]:
    get = raw.get if isinstance(raw, dict) else lambda k, d=None: getattr(
        raw, k, d)
    item: dict[str, Any] = {"code": str(get("code") or "unknown")}
    item["feature"] = str(get("feature") or feature)
    item["path"] = get("path") or get("phase")
    item["field"] = get("field")
    if get("unlock"):
        item["unlock"] = str(get("unlock"))
    return item


def to_gate(feature: str, phase: str, report: Any,
            *, evaluator: str = "sparkforge_azure") -> dict[str, Any]:
    """Native check()/evaluate() result → ``forge/SDDGate/v1``."""
    get = report.get if isinstance(report, dict) else lambda k, d=None: (
        getattr(report, k, d))
    ok = bool(get("ok", not get("refused") and not get("unresolved")))
    return {
        "schema": "forge/SDDGate/v1",
        "feature": feature,
        "phase": map_phase(phase),
        "ok": ok,
        "refused": [_item(r, feature) for r in get("refused") or ()],
        "unresolved": [
            _item(r, feature) for r in get("unresolved") or ()
        ],
        "evaluator": evaluator,
    }


def to_evidence(path: str | Path, *, kind: str, agent: str,
                command: list[str], covers: list[str] | None = None,
                sha256: str | None = None) -> dict[str, Any]:
    """Artifact reference → ``forge/Evidence/v1``."""
    p = Path(path)
    if sha256 is None and p.is_file():
        sha256 = f"sha256:{hashlib.sha256(p.read_bytes()).hexdigest()}"
    out: dict[str, Any] = {
        "schema": "forge/Evidence/v1",
        "id": p.stem,
        "kind": kind,
        "path": str(path),
        "produced_by": {"agent": agent, "command": list(command)},
        "covers": list(covers or []),
    }
    if sha256:
        out["sha256"] = sha256
    return out


def to_receipt(feature: str, phase: str, action: str, actor: str,
               recorded_at: str, *, verdict: str | None = None,
               outputs: list[str] | None = None,
               inputs_sha256: list[str] | None = None,
               rollback_ref: str | None = None,
               override: dict[str, Any] | None = None) -> dict[str, Any]:
    """Phase completion → ``forge/SDDReceipt/v1``."""
    out: dict[str, Any] = {
        "schema": "forge/SDDReceipt/v1",
        "feature": feature,
        "phase": map_phase(phase),
        "action": action,
        "actor": actor,
        "recorded_at": recorded_at,
    }
    if verdict is not None:
        out["verdict"] = verdict
    if outputs:
        out["outputs"] = list(outputs)
    if inputs_sha256:
        out["inputs_sha256"] = list(inputs_sha256)
    if rollback_ref:
        out["rollback_ref"] = rollback_ref
    if override:
        out["override"] = dict(override)
    return out


def federated_view(feature_dir: str | Path, *, feature: str,
                   agent: str = "sparkforge_azure") -> dict[str, Any]:
    """Best-effort projection — emits only artifacts that exist."""
    root = Path(feature_dir)
    out: dict[str, list[dict[str, Any]]] = {
        "forge/Evidence/v1": [],
        "forge/SDDReceipt/v1": [],
    }
    receipts = root / "receipts"
    if receipts.is_dir():
        for f in sorted(receipts.glob("*.json")):
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(doc, dict) and str(
                doc.get("schema", "")
            ).startswith("forge/SDDReceipt"):
                out["forge/SDDReceipt/v1"].append(doc)
    return {k: v for k, v in out.items() if v}
