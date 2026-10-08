"""Agent admin tools on the MCP surface (SDD MCP_AGENT_ADMIN).

``sfa_agents_list`` and ``sfa_agents_explain_route`` expose the same
``inventory()``/``explain_route()`` engines as the CLI — read-only.
"""
from __future__ import annotations

from sparkforge_azure.mcp.dispatch import call_tool
from sparkforge_azure.mcp.tools import TOOLS, load_all
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS


def test_sfa_agents_list() -> None:
    result = call_tool("sfa_agents_list", {})
    assert result.is_error is False
    payload = result.structured_content
    assert {a["agent_id"] for a in payload["agents"]} == set(ALL_AGENT_IDS)
    assert sum(payload["counts"].values()) == len(ALL_AGENT_IDS)


def test_sfa_agents_explain_route() -> None:
    result = call_tool(
        "sfa_agents_explain_route",
        {"prompt": "grant no unity catalog permission denied external location"},
    )
    assert result.is_error is False
    decisions = {r["specialist"]: r for r in result.structured_content["route"]}
    assert decisions["unity-catalog-specialist"]["decision"] == "selected"
    assert decisions["unity-catalog-specialist"]["matched_terms"]

    empty = call_tool("sfa_agents_explain_route", {})
    assert empty.is_error is True
    assert empty.structured_content["error"]["code"] == "invalid_input"


def test_agent_tools_are_read_only() -> None:
    load_all()
    for name in ("sfa_agents_list", "sfa_agents_explain_route"):
        spec = TOOLS[name]
        assert spec.risk.read_only is True
        assert spec.risk.local_write is False
        assert spec.risk.cloud_read is False
    agent_tools = sorted(n for n in TOOLS if "agent" in n)
    assert agent_tools == ["sfa_agents_explain_route", "sfa_agents_list"]
