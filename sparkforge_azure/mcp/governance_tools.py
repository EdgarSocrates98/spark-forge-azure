"""MCP tools for multi-layer governance diagnosis. Offline, read-only."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.azure.governance import diagnose
from sparkforge_azure.mcp.tools import READ_ONLY, tool


@tool(
    "sfa_governance_diagnose",
    description=("Diagnose an Azure access scenario across Entra, Unity Catalog "
                 "binding/privileges, "
                 "storage credential, network, RBAC and ADLS ACL. Returns per-layer verdicts, "
                 "root cause, section-30 conflicts, facts and findings."),
    input_schema={"type": "object", "properties": {"scenario": {"type": "object"}},
                  "required": ["scenario"], "additionalProperties": False},
    risk=READ_ONLY, domain="governance", compact=True,
    output_schema={
        "type": "object",
        "required": ["status", "chain", "unresolved", "authority"],
        "properties": {
            "scenario": {"type": "string"},
            "status": {"type": "string", "enum": ["allowed", "denied", "unresolved"]},
            "effective_identity": {"type": "string"},
            "root_cause": {"type": ["object", "null"]},
            "conflicts": {"type": "array", "items": {"type": "string"}},
            "chain": {"type": "array", "items": {"type": "object"}},
            "unresolved": {"type": "array", "items": {"type": "string"}},
            "facts": {"type": "array"},
            "findings": {"type": "array"},
            "authority": {"type": "string"},
        },
    },
)
def governance_diagnose(args: Mapping[str, Any]) -> dict[str, Any]:
    return diagnose(args["scenario"]).to_dict()
