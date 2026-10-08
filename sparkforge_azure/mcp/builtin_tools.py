"""Built-in tools that every installation exposes (identity of the Forge)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure import __version__
from sparkforge_azure.mcp.tools import READ_ONLY, tool

_EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}

# `_trust` é injetado pelo envelope do dispatch em todo resultado — declarado
# aqui para que o outputSchema descreva o structuredContent completo.
_TRUST = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "authority": {"type": "string"},
        "taint": {"type": "string"},
    },
}


@tool(
    "sfa_version",
    description="Spark Forge Azure version and provider identity.",
    input_schema=_EMPTY,
    risk=READ_ONLY,
    domain="core",
    compact=True,
    output_schema={
        "type": "object",
        "required": ["engine", "version", "provider"],
        "properties": {
            "engine": {"type": "string"},
            "version": {"type": "string"},
            "provider": {"type": "string"},
            "domain": {"type": "string"},
            "_trust": _TRUST,
        },
    },
)
def version(_: Mapping[str, Any]) -> dict[str, Any]:
    return {"engine": "spark-forge-azure", "version": __version__, "provider": "azure",
            "domain": "data"}
