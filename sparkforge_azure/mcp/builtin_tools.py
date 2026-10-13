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


_AI_SCHEMA = {
    "type": "object",
    "properties": {
        "host": {
            "type": "string",
            "enum": ["claude", "devin", "codex", "all"],
            "default": "all",
        },
        "repo": {"type": "string"},
    },
    "additionalProperties": False,
}


@tool(
    "sfa_ai",
    description="Observe AI host state (binary, version, auth, repo "
                "integration). Read-only: launching a host is CLI+TTY only "
                "(`sparkforge-azure ai <host> --launch`), never via MCP.",
    input_schema=_AI_SCHEMA,
    risk=READ_ONLY,
    domain="core",
    compact=True,
    output_schema={
        "type": "object",
        "required": ["repo", "hosts", "launched"],
        "properties": {
            "repo": {"type": "string"},
            "hosts": {"type": "array", "items": {"type": "object"}},
            "launched": {"type": "boolean"},
            "launch_refused": {"type": "string"},
            "_trust": _TRUST,
        },
    },
)
def ai_observe(arguments: Mapping[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from sparkforge_azure.distribution.ai import ai_flow

    repo = Path(str(arguments.get("repo") or "."))
    return ai_flow(
        str(arguments.get("host") or "all"),
        repo=repo,
        launch=False,  # launch is a human boundary — CLI + TTY only
    )
