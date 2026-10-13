"""Agent tool surface — the single source for ``sfa_*`` tool identity.

Manifest ``tools:`` allow-lists are enforceable only if every declared name
resolves somewhere real. Two families exist:

  * **MCP tools** — the external surface, loaded from
    ``sparkforge_azure.mcp.tools.load_all()`` (never hardcoded here).
  * **Internal tools** — capabilities the runtime itself provides to agents
    (role verbs, CLI-backed operations, knowledge/graph verbs that are not
    exposed as MCP tools). Each entry names its anchor: the module or CLI
    verb that implements it. The anchor is documentation; membership in
    ``AGENT_INTERNAL_TOOLS`` is enforcement.

Adding a tool to a manifest without adding it here is a contract violation:
``validate_manifest`` and the agentic inventory both measure against
``known_tools()``. This is what keeps ``allowed_tools`` honest (spec §16,
§94-99).
"""

from __future__ import annotations

#: Internal agent tools -> anchor (module path or ``cli: <verb>``).
#: Membership is closed: a name not listed here resolves nowhere.
AGENT_INTERNAL_TOOLS: dict[str, str] = {
    # Agentic role verbs — runtime-provided, never MCP tools.
    "sfa_analyze": "sparkforge_azure.agentic (analyzer role verb)",
    "sfa_judge": "sparkforge_azure.agentic (judge role verb)",
    # CLI-backed capabilities exposed to agents under sfa_* names.
    "sfa_agentops_inspect": "cli: agentops inspect",
    "sfa_graph_build": "cli: graph build",
    "sfa_lab_run": "cli: lab run",
    "sfa_lab_verify": "cli: lab verify",
    "sfa_tokensave_diff": "cli: tokensave diff",
    "sfa_tokensave_refs": "cli: tokensave refs",
    # Knowledge verbs — pack selection and drift/coverage checks.
    "sfa_knowledge_select": "sparkforge_azure.knowledge_engine.packs.PackRegistry.select",
    "sfa_knowledge_check": "sparkforge_azure.knowledgebase.freshness",
}


def mcp_tool_names() -> set[str]:
    """The live external MCP surface; empty set when it cannot be loaded."""
    try:
        from sparkforge_azure.mcp.tools import load_all

        return set(load_all())
    except Exception:  # noqa: BLE001 - callers degrade, never raise
        return set()


def known_tools(*, include_mcp: bool = True) -> set[str]:
    """Every resolvable tool name: internal registry + (optionally) MCP."""
    names = set(AGENT_INTERNAL_TOOLS)
    if include_mcp:
        names |= mcp_tool_names()
    return names


__all__ = ["AGENT_INTERNAL_TOOLS", "known_tools", "mcp_tool_names"]
