"""MCP tools for the offline access diagnostic vertical."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from sparkforge_azure.azure.pipeline import run_case
from sparkforge_azure.fabric.pipeline import run_fabric_case
from sparkforge_azure.mcp.tools import READ_ONLY, tool
from sparkforge_azure.stream.pipeline import run_stream_case

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
        "case_meta": {"type": "object"},
        "failure_layer": {"type": ["string", "null"]},
        "diagnosis": {"type": "object"},
        "findings": {"type": "array"},
        "rules_skipped": {"type": "array"},
        "unresolved": {"type": "array"},
        "facts": {"type": "array"},
        "access_graph": {"type": "object"},
        "evidence_paths": {"type": "object"},
        "knowledge": {"type": "object"},
        "overhead": {"type": "object"},
        "context_quality": {"type": "object"},
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


_FABRIC_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "case": {"type": "string"},
        "case_meta": {"type": "object"},
        "failure_layer": {"type": ["string", "null"]},
        "diagnosis": {"type": "object"},
        "findings": {"type": "array"},
        "rules_skipped": {"type": "array"},
        "unresolved": {"type": "array"},
        "facts": {"type": "array"},
        "fabric_graph": {"type": "object"},
        "evidence_paths": {"type": "object"},
        "knowledge": {"type": "object"},
        "overhead": {"type": "object"},
        "context_quality": {"type": "object"},
        "trust": {"type": "object"},
        "receipt": {"type": "object"},
        "_trust": {"type": "object"},
    },
    "required": ["status", "failure_layer", "diagnosis", "receipt"],
}


@tool(
    "sfa_diagnose_fabric",
    description="Offline Microsoft Fabric diagnosis on a case bundle "
                "(workspace/OneLake security/shortcuts/Spark/capacity/"
                "pipeline -> failure_layer -> receipt)",
    input_schema=_BUNDLE_SCHEMA,
    output_schema=_FABRIC_OUTPUT_SCHEMA,
    risk=READ_ONLY,
    domain="access",
    compact=True,
)
def _diagnose_fabric(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
    bundle = str(arguments["bundle"])
    if not Path(bundle).is_dir():
        raise ValueError(f"bundle not found: {bundle}")
    return run_fabric_case(
        bundle, profile=str(arguments.get("profile") or "balanced"))


_STREAM_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "case": {"type": "string"},
        "case_meta": {"type": "object"},
        "failure_layer": {"type": ["string", "null"]},
        "diagnosis": {"type": "object"},
        "delivery": {"type": "object"},
        "findings": {"type": "array"},
        "rules_skipped": {"type": "array"},
        "unresolved": {"type": "array"},
        "facts": {"type": "array"},
        "stream_graph": {"type": "object"},
        "evidence_paths": {"type": "object"},
        "knowledge": {"type": "object"},
        "overhead": {"type": "object"},
        "context_quality": {"type": "object"},
        "trust": {"type": "object"},
        "receipt": {"type": "object"},
        "_trust": {"type": "object"},
    },
    "required": ["status", "failure_layer", "diagnosis", "receipt"],
}


@tool(
    "sfa_diagnose_stream",
    description="Offline streaming diagnosis on a case bundle (Event Hubs/"
                "consumer groups/checkpoints/Structured Streaming + Fabric "
                "RTI Eventstream/Eventhouse/Activator -> failure_layer -> "
                "receipt). Summaries and evidence refs only — never raw "
                "event payloads.",
    input_schema=_BUNDLE_SCHEMA,
    output_schema=_STREAM_OUTPUT_SCHEMA,
    risk=READ_ONLY,
    domain="stream",
    compact=True,
)
def _diagnose_stream(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
    bundle = str(arguments["bundle"])
    if not Path(bundle).is_dir():
        raise ValueError(f"bundle not found: {bundle}")
    return run_stream_case(
        bundle, profile=str(arguments.get("profile") or "balanced"))
