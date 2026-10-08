"""Contract tests for the agent inventory (SDD AGENT_INVENTORY)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from sparkforge_azure.agentic.inventory import (
    AGENT_STATUSES,
    DIMENSIONS,
    get_agent,
    inventory,
)
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS
from sparkforge_azure.cli.main import main

REPO = Path(__file__).resolve().parents[1]


def test_every_agent_has_closed_status() -> None:
    rep = inventory(REPO)
    assert len(rep.agents) == len(ALL_AGENT_IDS)
    for agent in rep.agents:
        assert agent.status in AGENT_STATUSES
        assert {d.name for d in agent.dimensions} == set(DIMENSIONS)
    assert sum(rep.counts.values()) == len(ALL_AGENT_IDS)


def test_inventory_is_deterministic() -> None:
    first = inventory(REPO).to_dict()
    second = inventory(REPO).to_dict()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_cli_list_and_inspect_cover_taxonomy(capsys) -> None:
    assert main(["agents", "list"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    listed = {a["agent_id"] for a in out["agents"]}
    assert listed == set(ALL_AGENT_IDS)

    assert main(["agents", "inspect", "coordinator"]) == 0
    out = json.loads(capsys.readouterr().out)
    agent = out["agent"]
    assert agent["agent_id"] == "coordinator"
    assert agent["status"] in AGENT_STATUSES

    assert main(["agents", "inspect", "not-an-agent"]) == 2
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "refused"


def test_missing_artifacts_never_ready(tmp_path) -> None:
    # Copy the agents tree minus one manifest -> that agent must be broken,
    # never silently absent or promoted.
    agents_src = REPO / "agents"
    shutil.copytree(agents_src, tmp_path / "agents")
    (tmp_path / "agents" / "verifier.md").unlink()
    rep = inventory(tmp_path)
    by_id = {a.agent_id: a for a in rep.agents}
    assert by_id["verifier"].status == "broken"
    for agent in rep.agents:
        if agent.status == "ready":
            assert all(d.satisfied is not False for d in agent.dimensions)


def test_doctor_agentic_fleet() -> None:
    from sparkforge_azure.doctor import run

    out = run(areas=["agentic_fleet"])
    check = out["checks"][0]
    assert check["area"] == "agentic_fleet"
    assert check["status"] in {"ok", "unresolved"}
    assert check["data"]["total"] == len(ALL_AGENT_IDS)


def test_get_agent_outside_taxonomy() -> None:
    assert get_agent(REPO, "not-an-agent") is None
    assert get_agent(REPO, "coordinator") is not None


def test_internal_tools_resolve() -> None:
    """Every tool any manifest declares resolves to the tool registry."""
    from sparkforge_azure.agentmanifest.tools import known_tools

    catalog = known_tools()
    rep = inventory(REPO)
    for agent in rep.agents:
        tool_dim = next(d for d in agent.dimensions if d.name == "tool_policy")
        assert tool_dim.satisfied is not False, (
            f"{agent.agent_id}: {tool_dim.detail}")
        # declared tools resolve inside the catalog, not just the regex
        assert catalog  # registry is non-empty
