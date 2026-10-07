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
)
def governance_diagnose(args: Mapping[str, Any]) -> dict[str, Any]:
    return diagnose(args["scenario"]).to_dict()
