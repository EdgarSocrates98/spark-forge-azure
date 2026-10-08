"""MCP tools for the offline access diagnostic vertical."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.azure.pipeline import run_case
from sparkforge_azure.mcp.tools import READ_ONLY, tool

_BUNDLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "bundle": {"type": "string",
                   "description": "case bundle directory (case.yaml + artifacts)"},
        "profile": {"type": "string",
                    "enum": ["economy", "balanced", "deep"], "default": "balanced"},
    },
    "required": ["bundle"],
    "additionalProperties": False,
}

_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "case": {"type": "string"},
        "failure_layer": {"type": ["string", "null"]},
        "diagnosis": {"type": "object"},
        "findings": {"type": "array"},
        "unresolved": {"type": "array"},
        "facts": {"type": "array"},
        "evidence_paths": {"type": "object"},
        "trust": {"type": "object"},
        "receipt": {"type": "object"},
        "_trust": {"type": "object"},
    },
    "required": ["status", "failure_layer", "diagnosis", "receipt"],
}


@tool(
    "sfa_diagnose_access",
    description="Offline UC/RBAC/ACL/network access diagnosis on a case bundle "
                "(facts -> governance layers -> failure_layer -> receipt)",
    input_schema=_BUNDLE_SCHEMA,
    output_schema=_OUTPUT_SCHEMA,
    risk=READ_ONLY,
    domain="access",

    compact=True,
)
def _diagnose_access(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
    bundle = str(arguments["bundle"])
    if not Path(bundle).is_dir():
        raise ValueError(f"bundle not found: {bundle}")
    # CaseError propagates as ValueError; dispatch converts it to a named error.
    return run_case(bundle, profile=str(arguments.get("profile") or "balanced"))
