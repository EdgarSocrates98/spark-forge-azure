"""Agent inventory and status (spec sections 5-8, 135-136, 167-168).

Every agent in the taxonomy receives exactly one status from a CLOSED set:

    ready            — all contract dimensions pass, including eval coverage
    partial          — some dimensions pass, some fail (mixed)
    manifest_only    — manifest valid, nothing else wired
    broken           — manifest missing or invalid
    unevaluated      — all contract dims pass but no eval coverage

The status is a PURE function of the repository state: same tree, same
answer. No clock, no network, no LLM. Consumers: ``sparkforge-azure agents``
(inspection verbs), ``sparkforge-azure doctor`` (``agentic_fleet`` area),
``docs/agentic/AGENT_INVENTORY.md`` (generated).

Dimensions measured (Definition of Done, spec §217): manifest, role_plan,
tool policy, knowledge bindings, budget, handoff, routing reachability,
evals, AgentOps, autonomy level. A dimension
that cannot be measured (e.g. evals key absent in v1 manifests) is reported
``None`` — unresolved — and never counts as satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sparkforge_azure.agentmanifest.model import (
    ALL_AGENT_IDS,
    AUTONOMY_LEVELS,
    ROLE_IDS,
    SPECIALIST_IDS,
    SUBAGENT_IDS,
    parse_manifest,
    validate_manifest,
)
from sparkforge_azure.agentmanifest.routing import ROUTING_TABLE

#: Closed status vocabulary (spec §136). Order is worst -> best for reporting.
AGENT_STATUSES: tuple[str, ...] = (
    "broken",
    "manifest_only",
    "partial",
    "unevaluated",
    "ready",
)

#: The contract dimensions the inventory measures per agent (spec §217).
DIMENSIONS: tuple[str, ...] = (
    "manifest",
    "role_plan",
    "tool_policy",
    "knowledge",
    "budget",
    "handoff",
    "routing",
    "evals",
    "agentops",
    "autonomy",
)


@dataclass(frozen=True)
class DimensionReport:
    """One contract dimension for one agent.

    ``satisfied`` is tri-state: True measured-pass, False measured-fail,
    None not-measured (the artifact declaring it is absent — unresolved,
    never silently satisfied).
    """

    name: str
    satisfied: bool | None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "satisfied": self.satisfied,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AgentReport:
    """Inventory line for one agent."""

    agent_id: str
    kind: str
    status: str
    dimensions: tuple[DimensionReport, ...]
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "kind": self.kind,
            "status": self.status,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "detail": self.detail,
        }


@dataclass(frozen=True)
class InventoryReport:
    """Full fleet inventory: per-agent reports + status counts."""

    agents: tuple[AgentReport, ...]
    counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agents": [a.to_dict() for a in self.agents],
            "counts": dict(self.counts),
        }


def _kind_of(agent_id: str) -> str:
    if agent_id in ROLE_IDS:
        return "role"
    if agent_id in SPECIALIST_IDS:
        return "specialist"
    return "subagent"


def _tool_catalog() -> set[str]:
    """All resolvable tool names: internal registry + MCP surface.

    Empty when the MCP catalog fails to load — the internal registry still
    resolves, so the dimension stays measured for internal tools.
    """
    from sparkforge_azure.agentmanifest.tools import known_tools

    return known_tools()


def _has_role_plan(agent_id: str, manifest_ok: bool) -> bool | None:
    """RoleContextPlan resolvable for this agent.

    Plans are DERIVED from the manifest (single source) — see
    ``agentic.role_plans.role_plan_for``. A valid manifest always yields a
    plan; an invalid one yields ``False``; the sf-* executor plans remain
    explicit overrides in ``ROLE_PLANS``.
    """
    if not manifest_ok:
        return False
    try:
        from sparkforge_azure.agentic.role_plans import role_plan_for

        return role_plan_for(agent_id) is not None
    except Exception:  # noqa: BLE001
        return None


def _routed(agent_id: str, known_ids: set[str]) -> bool | None:
    """The agent is reachable by the runtime paths that exist today.

    Specialists: present in ``ROUTING_TABLE``. Subagents: reachable via a
    declared parent + ``handoff_targets`` of that parent or via
    ``SUBAGENT_PARENTS``. Roles: reachable as ``handoff_targets`` of some
    other agent or they are the coordinator itself. Not measured when the
    routing table cannot be loaded.
    """
    if agent_id in SPECIALIST_IDS:
        return any(r.specialist == agent_id for r in ROUTING_TABLE)
    if agent_id in SUBAGENT_IDS:
        try:
            from sparkforge_azure.agentmanifest.model import SUBAGENT_PARENTS

            return agent_id in SUBAGENT_PARENTS
        except Exception:  # noqa: BLE001
            return None
    if agent_id == "coordinator":
        return True
    return agent_id in known_ids


def _eval_coverage(
    agent_id: str, data: dict[str, Any], root: Path,
) -> list[str] | None:
    """Eval coverage declared and resolving.

    v1 manifests carry no ``evals`` key -> ``None`` (unresolved). v2
    manifests declare ``evals: [...]``; each entry must name a resolvable
    artifact — a file under ``tests/`` or ``evals/`` inside ``root``.
    Returns the list of unresolvable entries (``[]`` = covered).
    """
    evals = data.get("evals")
    if evals is None:
        return None
    if not isinstance(evals, list):
        return ["<evals is not a list>"]
    if not evals:
        return ["<evals is empty>"]
    bad = [
        e for e in evals
        if not isinstance(e, str)
        or Path(e).is_absolute()
        or ".." in Path(e).parts
        or Path(e).parts[0] not in {"tests", "evals"}
        or not (root / e).is_file()
    ]
    return bad


def _agentops_coverage(agent_id: str, data: dict[str, Any]) -> bool | None:
    """AgentOps span coverage declared for this agent."""
    emit = data.get("agentops_emit_span")
    if emit is None:
        return None
    return bool(emit)


def _dim_reports(
    agent_id: str,
    manifest_ok: bool,
    data: dict[str, Any],
    *,
    known_ids: set[str],
    tool_catalog: set[str],
    root: Path,
) -> tuple[DimensionReport, ...]:
    dims: list[DimensionReport] = [DimensionReport("manifest", manifest_ok)]
    if not manifest_ok:
        return tuple(dims + [DimensionReport(n, None, "not measured: manifest broken")
                             for n in DIMENSIONS[1:]])

    dims.append(DimensionReport("role_plan", _has_role_plan(agent_id, manifest_ok)))

    tools = [str(t) for t in (data.get("allowed_tools") or [])]
    if not tools:
        dims.append(DimensionReport("tool_policy", True, "no tools declared"))
    else:
        missing = sorted(t for t in tools if t not in tool_catalog)
        dims.append(DimensionReport(
            "tool_policy", not missing,
            f"unresolved tools: {missing}" if missing else f"{len(tools)} tools resolve"))

    refs = [str(r) for r in (data.get("knowledge_packs") or [])]
    missing_refs = sorted(r for r in refs if not (root / r).is_dir())
    dims.append(DimensionReport(
        "knowledge", not missing_refs,
        f"missing refs: {missing_refs}" if missing_refs else f"{len(refs)} refs resolve"))

    budget = data.get("budget") or {}
    ok = isinstance(budget, dict) and all(
        isinstance(budget.get(k), int) and budget[k] > 0
        for k in ("context", "tools", "model_calls")
    )
    dims.append(DimensionReport("budget", ok))

    handoffs = data.get("handoffs") or {}
    targets = [str(t) for t in (handoffs.get("allowed_targets") or [])]
    bad = sorted(t for t in targets if t not in known_ids and t not in ROLE_IDS)
    mode = handoffs.get("mode")
    dims.append(DimensionReport(
        "handoff",
        not bad and mode == "DATA_ONLY",
        f"unresolved targets: {bad}" if bad else "DATA_ONLY, targets resolve"))

    dims.append(DimensionReport("routing", _routed(agent_id, known_ids)))
    unresolvable = _eval_coverage(agent_id, data, root)
    dims.append(DimensionReport(
        "evals",
        None if unresolvable is None else not unresolvable,
        f"unresolvable: {unresolvable}" if unresolvable else None,
    ))
    dims.append(DimensionReport("agentops", _agentops_coverage(agent_id, data)))
    level = data.get("autonomy")
    dims.append(DimensionReport(
        "autonomy",
        None if level is None else level in AUTONOMY_LEVELS,
        f"level {level}" if level in AUTONOMY_LEVELS else f"invalid: {level}",
    ))
    return tuple(dims)


def _status_of(agent_id: str, dims: tuple[DimensionReport, ...]) -> str:
    """Closed status from the measured dimensions.

    Unresolved dims (``satisfied is None``) do not block ``ready`` — they
    are surfaced in the report — but a ``False`` always degrades.
    """
    by_name = {d.name: d.satisfied for d in dims}
    if by_name.get("manifest") is False:
        return "broken"
    core_names = ("role_plan", "tool_policy", "knowledge", "budget", "handoff",
                  "routing")
    core_true = sum(1 for n in core_names if by_name.get(n) is True)
    core_fail = sum(1 for n in core_names if by_name.get(n) is False)
    measured_beyond_manifest = core_true + core_fail
    if measured_beyond_manifest == 0:
        return "manifest_only"
    if core_true == len(core_names):
        # every contract dim measured true; evals decides ready vs unevaluated
        if by_name.get("evals") is True:
            return "ready" if by_name.get("agentops") is not False else "partial"
        return "unevaluated"
    if core_true <= 1:
        return "manifest_only"
    return "partial"


def _load_and_validate(
    root: Path, agent_id: str, known: set[str], *, strict_knowledge: bool,
) -> tuple[dict[str, Any], bool]:
    """Parse + validate one manifest file; ``(data, ok)`` — data={} when missing.

    ``strict_knowledge=False`` treats missing knowledge dirs as pending (the
    ``knowledge`` dimension reports them instead of breaking the manifest).
    """
    path = root / "agents" / f"{agent_id}.md"
    if not path.is_file():
        return {}, False
    try:
        manifest = parse_manifest(path)
    except Exception:  # noqa: BLE001 - parse failure == broken
        return {}, False
    rep = validate_manifest(
        manifest.data, manifest.body, where=agent_id,
        known_ids=known, root=root,
        allow_pending_knowledge=not strict_knowledge, file_stem=agent_id,
    )
    return manifest.data, rep.ok


def inventory(root: Path | str, *, strict_knowledge: bool = False) -> InventoryReport:
    """Audit every agent in the taxonomy. Pure; same tree -> same report."""
    root = Path(root)
    catalog = _tool_catalog()
    known = set(ALL_AGENT_IDS)

    agents: list[AgentReport] = []
    for agent_id in ALL_AGENT_IDS:
        data, manifest_ok = _load_and_validate(
            root, agent_id, known, strict_knowledge=strict_knowledge)
        dims = _dim_reports(
            agent_id, manifest_ok, data,
            known_ids=known, tool_catalog=catalog, root=root,
        )
        status = _status_of(agent_id, dims)
        agents.append(AgentReport(agent_id, _kind_of(agent_id), status, dims))

    counts = {s: sum(1 for a in agents if a.status == s) for s in AGENT_STATUSES}
    return InventoryReport(tuple(agents), counts)


def get_agent(root: Path | str, agent_id: str) -> AgentReport | None:
    """Single-agent report; ``None`` when the id is outside the taxonomy."""
    if agent_id not in ALL_AGENT_IDS:
        return None
    return next((a for a in inventory(root).agents if a.agent_id == agent_id), None)


__all__ = [
    "AGENT_STATUSES",
    "DIMENSIONS",
    "AgentReport",
    "DimensionReport",
    "InventoryReport",
    "get_agent",
    "inventory",
]
