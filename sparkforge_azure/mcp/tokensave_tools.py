"""MCP tools for TokenSave. All read-only; workspace-confined."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.mcp.tools import READ_ONLY, tool
from sparkforge_azure.tokensave import TokenSave

_ROOT = {"type": "string", "description": "workspace root", "default": "."}
_PROFILE = {"type": "string", "enum": ["economy", "balanced", "deep"], "default": "economy"}


def _ts(args: Mapping[str, Any]) -> TokenSave:
    return TokenSave(args.get("root", "."), profile_name=args.get("profile", "economy"),
                     index_db=args.get("index"))


@tool(
    "sfa_tokensave_context",
    description="Minimal sufficient context for a task via the L0-L6 retrieval ladder.",
    input_schema={"type": "object", "properties": {
        "task": {"type": "string"}, "root": _ROOT, "profile": _PROFILE,
        "index": {"type": "string"}, "terms": {"type": "array", "items": {"type": "string"}}},
        "required": ["task"], "additionalProperties": False},
    risk=READ_ONLY, domain="tokensave", compact=True,
)
def context(args: Mapping[str, Any]) -> dict[str, Any]:
    return _ts(args).context(args["task"], required_terms=args.get("terms")).to_dict()


@tool(
    "sfa_tokensave_search",
    description="L1 literal search; returns path, line and the matching line only.",
    input_schema={"type": "object", "properties": {
        "query": {"type": "string"}, "root": _ROOT, "profile": _PROFILE,
        "limit": {"type": "integer", "minimum": 1}},
        "required": ["query"], "additionalProperties": False},
    risk=READ_ONLY, domain="tokensave", compact=True,
)
def search(args: Mapping[str, Any]) -> dict[str, Any]:
    ts = _ts(args)
    hits = ts.search(args["query"], limit=args.get("limit"))
    return {"hits": hits, "ledger": ts.ledger.summary()}


@tool(
    "sfa_tokensave_read",
    description="L5 bounded slice of a file (line window capped by profile).",
    input_schema={"type": "object", "properties": {
        "path": {"type": "string"}, "start": {"type": "integer", "minimum": 1},
        "end": {"type": "integer", "minimum": 1}, "root": _ROOT, "profile": _PROFILE},
        "required": ["path"], "additionalProperties": False},
    risk=READ_ONLY, domain="tokensave",
)
def read(args: Mapping[str, Any]) -> dict[str, Any]:
    return _ts(args).read(args["path"], args.get("start", 1), args.get("end"))


@tool(
    "sfa_tokensave_symbols",
    description="L2 symbols (names and line ranges, no bodies) of one file.",
    input_schema={"type": "object", "properties": {
        "path": {"type": "string"}, "root": _ROOT},
        "required": ["path"], "additionalProperties": False},
    risk=READ_ONLY, domain="tokensave",
)
def symbols(args: Mapping[str, Any]) -> dict[str, Any]:
    out = _ts(args).symbols(args["path"])
    return out if isinstance(out, dict) else {"symbols": out}
