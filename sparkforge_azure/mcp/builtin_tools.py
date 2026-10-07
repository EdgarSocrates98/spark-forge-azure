"""Built-in tools that every installation exposes (identity of the Forge)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure import __version__
from sparkforge_azure.mcp.tools import READ_ONLY, tool

_EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}


@tool(
    "sfa_version",
    description="Spark Forge Azure version and provider identity.",
    input_schema=_EMPTY,
    risk=READ_ONLY,
    domain="core",
    compact=True,
)
def version(_: Mapping[str, Any]) -> dict[str, Any]:
    return {"engine": "spark-forge-azure", "version": __version__, "provider": "azure",
            "domain": "data"}
