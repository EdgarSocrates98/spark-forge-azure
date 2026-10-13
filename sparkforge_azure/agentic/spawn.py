"""Spawn gate — SPAWN | SKIP | DEFER per agent (spec §22-24, §136).

The coordinator routes specialists deterministically; the spawn gate decides
whether each *candidate* actually earns its context window. A decision is a
pure function of the manifest's ``spawn`` block plus a ``SpawnContext``
snapshot — no model, no clock, no network.

Semantics (spec AC): no domain match or no domain-scoped unresolved ->
``SKIP``; routed domain with unresolved uncertainty -> ``SPAWN``; inputs not
yet producible -> ``DEFER``. ``information_gain_threshold`` from the manifest
gates SPAWN: expected gain below the threshold degrades SPAWN to ``SKIP``
(the agent would burn budget without resolving anything).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sparkforge_azure.agentmanifest.model import (
    ALL_AGENT_IDS,
    parse_manifest,
)

#: Closed decision vocabulary.
SPAWN_DECISIONS: tuple[str, ...] = ("SPAWN", "SKIP", "DEFER")


@dataclass(frozen=True)
class SpawnContext:
    """Case snapshot the gate evaluates — all fields are DATA."""

    routed_specialists: tuple[str, ...] = ()
    #: Unresolved item ids, optionally ``"<domain>:<text>"``-prefixed.
    unresolved: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    completed_agents: tuple[str, ...] = ()
    spawned_parents: tuple[str, ...] = ()
    gate_requested: bool = False


@dataclass(frozen=True)
class SpawnDecision:
    """One agent's spawn verdict — closed decision + machine-readable reason."""

    agent_id: str
    decision: str
    reason: str
    expected_gain: float | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "decision": self.decision,
            "reason": self.reason,
            "expected_gain": self.expected_gain,
            "details": dict(self.details),
        }


def _manifest_data(root: Path | str, agent_id: str) -> dict[str, Any]:
    path = Path(root) / "agents" / f"{agent_id}.md"
    if not path.is_file():
        return {}
    try:
        return parse_manifest(path).data
    except Exception:  # noqa: BLE001 - gate refuses closed, never raises
        return {}


def _scoped_unresolved(data: dict[str, Any], ctx: SpawnContext) -> list[str]:
    """Unresolved items in the agent's declared domain scope."""
    domain = str(data.get("domain", ""))
    planes = ("control", "evidence", "review", "adversarial", "test_eval")
    if not domain or domain in planes:
        return list(ctx.unresolved)
    return [u for u in ctx.unresolved if domain in u]


def _gain_for(condition: str, data: dict[str, Any], ctx: SpawnContext) -> float:
    """Expected information gain in [0, 1], measured per condition kind —
    what the agent would actually work on if spawned:

    * spine roles (``always``) and explicit eval gates: 1.0 — always earn it
    * ``on_finding_review`` / ``on_disagreement`` / ``on_conflict``: presence
      of their input artifact is the gain signal
    * ``on_domain_match`` / ``on_parent_spawn``: fraction of unresolved items
      inside the agent's declared domain
    """
    if condition == "always":
        return 1.0
    if condition == "on_gate":
        return 1.0 if ctx.gate_requested else 0.0
    if condition == "on_finding_review":
        return 1.0 if ctx.findings else 0.0
    if condition in ("on_disagreement", "on_conflict"):
        return 1.0 if ctx.conflicts else 0.0
    scoped = _scoped_unresolved(data, ctx)
    if not ctx.unresolved or not scoped:
        return 0.0
    return round(min(1.0, len(scoped) / len(ctx.unresolved)), 3)


def decide_spawn(
    agent_id: str,
    ctx: SpawnContext,
    *,
    root: Path | str = ".",
) -> SpawnDecision:
    """The gate. Pure: same (agent, ctx, tree) -> same decision."""
    if agent_id not in ALL_AGENT_IDS:
        return SpawnDecision(agent_id, "SKIP", "agent_not_in_taxonomy")
    data = _manifest_data(root, agent_id)
    if not data:
        return SpawnDecision(agent_id, "SKIP", "manifest_unavailable")
    if agent_id in ctx.completed_agents:
        return SpawnDecision(agent_id, "SKIP", "already_completed")

    conditions = [str(c) for c in data.get("spawn", {}).get("conditions", [])]
    threshold = float(data.get("spawn", {}).get("information_gain_threshold", 0) or 0)
    details: dict[str, Any] = {"conditions": conditions, "threshold": threshold}

    def gated(decision: str, reason: str, gain: float) -> SpawnDecision:
        if decision == "SPAWN" and gain < threshold:
            return SpawnDecision(
                agent_id, "SKIP", "below_information_gain_threshold",
                expected_gain=gain, details=details)
        return SpawnDecision(agent_id, decision, reason, expected_gain=gain,
                             details=details)

    for cond in conditions:
        gain = _gain_for(cond, data, ctx)
        if cond == "always":
            return gated("SPAWN", "spine_role_always_spawned", gain)
        if cond == "on_domain_match":
            if agent_id in ctx.routed_specialists:
                if ctx.unresolved:
                    return gated("SPAWN", "routed_with_unresolved_in_scope", gain)
                return SpawnDecision(agent_id, "DEFER",
                                     "routed_but_no_unresolved_yet",
                                     expected_gain=gain, details=details)
            continue
        if cond == "on_finding_review":
            if ctx.findings:
                return gated("SPAWN", "findings_ready_for_review", gain)
            continue
        if cond == "on_disagreement":
            if ctx.conflicts:
                return gated("SPAWN", "disagreement_present", gain)
            continue
        if cond == "on_conflict":
            if ctx.conflicts:
                return gated("SPAWN", "genuine_conflict", gain)
            continue
        if cond == "on_parent_spawn":
            from sparkforge_azure.agentmanifest.model import SUBAGENT_PARENTS
            parent = SUBAGENT_PARENTS.get(agent_id)
            if parent and parent in ctx.spawned_parents:
                return gated("SPAWN", "parent_delegated_scope", gain)
            return SpawnDecision(agent_id, "DEFER", "parent_not_spawned",
                                 expected_gain=gain, details=details)
        if cond == "on_gate":
            if ctx.gate_requested:
                return gated("SPAWN", "eval_gate_requested", gain)
            continue
    # No condition fired: agents whose inputs cannot exist yet DEFER; the rest SKIP.
    if conditions:
        return SpawnDecision(agent_id, "DEFER", "conditions_unmet_inputs_pending",
                             details=details)
    return SpawnDecision(agent_id, "SKIP", "no_spawn_conditions",
                         details=details)


def decide_team(
    agent_ids: list[str] | tuple[str, ...],
    ctx: SpawnContext,
    *,
    root: Path | str = ".",
) -> list[SpawnDecision]:
    """Gate a list of candidates, in order. Deterministic."""
    return [decide_spawn(a, ctx, root=root) for a in agent_ids]


__all__ = [
    "SPAWN_DECISIONS",
    "SpawnContext",
    "SpawnDecision",
    "decide_spawn",
    "decide_team",
]
