"""Agent teams — eligibility files and privilege audit (SDD AGENT_TEAMS)."""
from __future__ import annotations

import shutil
from pathlib import Path

from sparkforge_azure.agentic.spawn import SpawnContext, decide_spawn
from sparkforge_azure.agentic.teams import (
    NON_DOMAIN_FAMILIES,
    audit_teams,
    load_team,
    load_teams,
    team_for_domain,
)
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS, load_manifests

REPO = Path(__file__).resolve().parents[1]
TEAMS = REPO / "agent-teams"


def test_team_files_validate() -> None:
    teams = load_teams(REPO)
    assert {t.name for t in teams} == {"databricks", "fabric", "streaming", "migration"}
    reports = audit_teams(REPO)
    assert all(errs == [] for errs in reports.values()), reports
    for team in teams:
        assert set(team.eligible) <= set(ALL_AGENT_IDS), team.name


def test_team_audit_detects_privilege_enlargement(tmp_path) -> None:
    # member entry declaring tools the manifest does not have -> refused
    shutil.copytree(TEAMS, tmp_path / "agent-teams")
    bad = tmp_path / "agent-teams" / "evil.yaml"
    bad.write_text(
        "team: evil\ndomain: fabric\nmission: x\n"
        "eligible: [fabric-specialist]\n"
        "extra_tools: [sfa_lab_run]\n"
        "rules: {max_specialists: 3}\n",
        encoding="utf-8")
    reports = audit_teams(tmp_path)
    assert any("privilege keys" in e for e in reports["evil"])

    # per-member overrides are forbidden outright
    members = tmp_path / "agent-teams" / "members.yaml"
    members.write_text(
        "team: members\ndomain: fabric\nmission: x\n"
        "eligible: [fabric-specialist]\n"
        "members: [{id: fabric-specialist, extra_tools: [sfa_lab_run]}]\n"
        "rules: {max_specialists: 3}\n",
        encoding="utf-8")
    reports = audit_teams(tmp_path)
    assert any("per-member overrides" in e for e in reports["members"])

    # eligible outside the taxonomy -> refused
    ghost = tmp_path / "agent-teams" / "ghost.yaml"
    ghost.write_text(
        "team: ghost\ndomain: fabric\nmission: x\n"
        "eligible: [fabric-specialist, not-an-agent]\n"
        "rules: {max_specialists: 3}\n",
        encoding="utf-8")
    reports = audit_teams(tmp_path)
    assert any("not in taxonomy" in e for e in reports["ghost"])


def test_eligible_is_not_spawned() -> None:
    """Membership narrows candidates; the spawn gate still decides."""
    team = load_team(TEAMS / "databricks.yaml")
    ctx = SpawnContext()  # nothing routed, nothing unresolved
    for member in team.eligible:
        d = decide_spawn(member, ctx, root=REPO)
        assert d.decision != "SPAWN", (member, d)


def test_control_and_eval_planes_not_in_domain_teams() -> None:
    manifests = {m.id: m for m in load_manifests(REPO)}
    for team in load_teams(REPO):
        for member in team.eligible:
            fam = str(manifests[member].data["family"])
            assert fam not in NON_DOMAIN_FAMILIES, (team.name, member, fam)
    # reviewers of the review plane may only join as subagents (review family
    # is allowed for subagents — but never control/evidence/adversarial/test_eval)
    for tid in ("coordinator", "test-engineer", "evaluation-specialist",
                "critic", "referee"):
        for team in load_teams(REPO):
            assert tid not in team.eligible


def test_subagents_need_parent_in_team() -> None:
    team = load_team(TEAMS / "databricks.yaml")
    subs = [m for m in team.eligible if m.startswith("databricks-")]
    assert "azure-databricks-specialist" in team.eligible
    assert len(subs) == 4


def test_team_for_domain_lookup() -> None:
    assert team_for_domain(REPO, "fabric").name == "fabric"
    assert team_for_domain(REPO, "not-a-domain") is None
