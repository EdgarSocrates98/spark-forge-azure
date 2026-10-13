"""Agent teams — eligibility declarations under ``agent-teams/*.yaml``.

A team file answers one question: which agents MAY be composed for a domain
case. It is not a spawn list — the spawn gate (``agentic/spawn.py``) still
decides, per candidate, whether running it earns its budget. Teams narrow
the candidate set; they never widen privileges.

``audit_team`` enforces the contract:

* ``eligible`` ⊆ the agent taxonomy;
* no control/evidence/adversarial/test_eval member as ``eligible`` — those
  planes are spawned by the runtime, never by team membership;
* subagents require their declared parent to be eligible too;
* ``rules.max_specialists`` within the routing ceiling;
* a team file must not enlarge a member's manifest (no per-member tool,
  context, budget or trust overrides — the audit flags any such key).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.agentmanifest.model import (
    ALL_AGENT_IDS,
    SUBAGENT_PARENTS,
    load_manifests,
)
from sparkforge_azure.agentmanifest.routing import MAX_AGENTS_CEILING

TEAMS_DIR = "agent-teams"
REQUIRED_KEYS: tuple[str, ...] = (
    "team", "domain", "mission", "eligible", "rules")
RULE_KEYS: tuple[str, ...] = (
    "max_specialists", "subagents_require_parent", "reviewers_conditional")
#: Keys that would enlarge a member's privilege if present inside a member
#: entry or at top level besides the schema — the audit flags every one.
PRIVILEGE_KEYS: frozenset[str] = frozenset({
    "allowed_tools", "denied_tools", "tools", "allowed_context_kinds",
    "allowed_context", "required_context_kinds", "required_context",
    "budget", "trust_floor", "risk", "grants", "extra_tools",
})
#: Families that must never appear as ``eligible`` in a domain team — they
#: join cases through the runtime spine and conditional gates, not membership.
NON_DOMAIN_FAMILIES: frozenset[str] = frozenset({
    "control", "evidence", "adversarial", "test_eval"})


@dataclass(frozen=True)
class Team:
    name: str
    domain: str
    mission: str
    eligible: tuple[str, ...]
    rules: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "team": self.name,
            "domain": self.domain,
            "mission": self.mission,
            "eligible": list(self.eligible),
            "rules": dict(self.rules),
        }


def load_team(path: Path | str) -> Team:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: team file must be a mapping")
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"{path}: missing keys {missing}")
    return Team(
        name=str(data["team"]),
        domain=str(data["domain"]),
        mission=str(data["mission"]),
        eligible=tuple(str(a) for a in data["eligible"]),
        rules=dict(data.get("rules") or {}),
    )


def discover_teams(root: Path | str) -> list[Path]:
    base = Path(root) / TEAMS_DIR
    if not base.is_dir():
        return []
    return sorted(base.glob("*.yaml"))


def load_teams(root: Path | str) -> list[Team]:
    return [load_team(p) for p in discover_teams(root)]


def _family_of(manifests: dict[str, Any], agent_id: str) -> str:
    m = manifests.get(agent_id)
    return str(m.data.get("family", "")) if m else ""


def audit_team(team: Team, root: Path | str, *, path: Path | None = None) -> list[str]:
    """The privilege + taxonomy audit. Returns refusal strings, [] when clean."""
    root = Path(root)
    errors: list[str] = []
    where = f"{team.name} ({path.name})" if path else team.name

    manifests = {m.id: m for m in load_manifests(root)}
    known = set(ALL_AGENT_IDS)

    for member in team.eligible:
        if member not in known:
            errors.append(f"{where}: eligible member {member!r} not in taxonomy")
            continue
        fam = _family_of(manifests, member)
        if fam in NON_DOMAIN_FAMILIES:
            errors.append(
                f"{where}: {member!r} has family {fam!r} — never eligible in a domain team")

    for sub, parent in SUBAGENT_PARENTS.items():
        if sub in team.eligible and parent not in team.eligible:
            errors.append(f"{where}: subagent {sub!r} eligible without parent {parent!r}")

    rules = team.rules or {}
    unknown_rules = sorted(set(rules) - set(RULE_KEYS))
    if unknown_rules:
        errors.append(f"{where}: unknown rules {unknown_rules}")
    cap = rules.get("max_specialists")
    if not isinstance(cap, int) or not 1 <= cap <= MAX_AGENTS_CEILING:
        errors.append(f"{where}: rules.max_specialists must be 1..{MAX_AGENTS_CEILING}")

    # privilege enlargement: raw file must not carry member overrides
    if path is not None:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        hits = sorted(set(raw) & PRIVILEGE_KEYS)
        if hits:
            errors.append(f"{where}: privilege keys in team file {hits}")
        members = raw.get("members")
        if members is not None:
            errors.append(f"{where}: per-member overrides are forbidden "
                          "(privileges live in the manifests only)")
    return errors


def audit_teams(root: Path | str) -> dict[str, list[str]]:
    """Audit every team file under ``agent-teams/``; name -> refusals."""
    out: dict[str, list[str]] = {}
    for path in discover_teams(root):
        try:
            team = load_team(path)
        except ValueError as exc:
            out[path.stem] = [str(exc)]
            continue
        out[team.name] = audit_team(team, root, path=path)
    return out


def team_for_domain(root: Path | str, domain: str) -> Team | None:
    """The team whose ``domain`` matches, or None."""
    for team in load_teams(root):
        if team.domain == domain:
            return team
    return None


__all__ = [
    "NON_DOMAIN_FAMILIES",
    "PRIVILEGE_KEYS",
    "RULE_KEYS",
    "TEAMS_DIR",
    "Team",
    "audit_team",
    "audit_teams",
    "discover_teams",
    "load_team",
    "load_teams",
    "team_for_domain",
]
