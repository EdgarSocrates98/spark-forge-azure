"""Autonomy field on the v2 manifest contract (SDD AGENT_AUTONOMY_FIELD).

§153-155: the default is BOUNDED — every agent declares its level and the
fleet never exceeds L2 without an explicit, reviewed exception.
"""
from __future__ import annotations

from pathlib import Path

from sparkforge_azure.agentic.autonomy import AutonomyLevel, get_profile
from sparkforge_azure.agentmanifest.model import (
    ALL_AGENT_IDS,
    ROLE_IDS,
    SPECIALIST_IDS,
    SUBAGENT_IDS,
    parse_manifest,
)

REPO = Path(__file__).resolve().parents[1]

LEVELS = {lvl.value for lvl in AutonomyLevel}

EXPECTED = {
    **{r: "L1" for r in SPECIALIST_IDS},
    "coordinator": "L2",
    "inventory": "L0",
    "extractor": "L0",
    "analyzer": "L0",
    "judge": "L0",
    "verifier": "L0",
    "referee": "L2",
}
EXPECTED.update({r: EXPECTED.get(r, "L1") for r in ROLE_IDS})
EXPECTED.update({s: "L1" for s in SUBAGENT_IDS})


def _autonomy(agent_id: str) -> str:
    return str(
        parse_manifest(REPO / "agents" / f"{agent_id}.md").data["autonomy"]
    )


def test_autonomy_declared_and_valid() -> None:
    for agent_id in ALL_AGENT_IDS:
        level = _autonomy(agent_id)
        assert level in LEVELS, f"{agent_id}: autonomy {level!r} not in L0..L5"
        assert level == EXPECTED[agent_id], (
            f"{agent_id}: autonomy {level} != expected {EXPECTED[agent_id]}"
        )


def test_fleet_cap_l2() -> None:
    order = sorted(LEVELS)  # L0 < L1 < ... < L5 lexicographically
    cap = order.index("L2")
    for agent_id in ALL_AGENT_IDS:
        assert order.index(_autonomy(agent_id)) <= cap, (
            f"{agent_id} above L2 — §153 default is BOUNDED"
        )


def test_declared_level_resolves_profile() -> None:
    for agent_id in ALL_AGENT_IDS:
        profile = get_profile(AutonomyLevel(_autonomy(agent_id)))
        assert profile is not None
        assert profile.level.value == _autonomy(agent_id)


def test_autonomy_for_is_fail_closed() -> None:
    from sparkforge_azure.agentic.autonomy import autonomy_for

    assert autonomy_for("coordinator", REPO) == AutonomyLevel.L2_COOPERATIVE
    assert autonomy_for("unity-catalog-specialist", REPO) == (
        AutonomyLevel.L1_SPECIALIST
    )
    assert autonomy_for("not-an-agent", REPO) == AutonomyLevel.L0_DETERMINISTIC
    assert autonomy_for("coordinator", REPO / "nonexistent") == (
        AutonomyLevel.L0_DETERMINISTIC
    )
