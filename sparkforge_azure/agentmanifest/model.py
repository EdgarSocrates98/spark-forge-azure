"""Agent / specialist manifest contract (sections 94-99).

Each agent lives in ``agents/<id>.md`` with a YAML front matter manifest. Validation is
deterministic and offline. Handoffs between agents are always ``DATA_ONLY`` (no instruction
crosses an agent boundary), risk is never ``cloud_write``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sparkforge_azure.skills.model import (
    SKILL_NAMES,
    FrontMatterError,
    body_line_count,
    knowledge_ref_exists,
    rel_label,
    split_front_matter,
    validate_knowledge_ref,
)

KINDS: tuple[str, ...] = ("role", "specialist", "subagent")

#: Closed family vocabulary (contract v2): which plane the agent belongs to.
#:   control      — routes, budgets, stops (coordinator)
#:   evidence     — facts -> evidence -> verdict -> report spine
#:   domain       — the twenty specialists
#:   review       — reviewers and bounded subagent reviewers
#:   adversarial  — critic + referee
#:   test_eval    — test-engineer + evaluation-specialist (off hot path)
FAMILIES: tuple[str, ...] = (
    "control",
    "evidence",
    "domain",
    "review",
    "adversarial",
    "test_eval",
)
#: family allowed per kind — a specialist is never `evidence`, a role never `domain`.
FAMILY_BY_KIND: dict[str, tuple[str, ...]] = {
    "role": ("control", "evidence", "review", "adversarial", "test_eval"),
    "specialist": ("domain",),
    "subagent": ("review",),
}

ROLE_IDS: tuple[str, ...] = (
    "coordinator",
    "inventory",
    "extractor",
    "analyzer",
    "judge",
    "verifier",
    "reviewer",
    "critic",
    "referee",
    "synthesizer",
    "security-reviewer",
    "cost-reviewer",
    "performance-reviewer",
    "migration-reviewer",
    "test-engineer",
    "evaluation-specialist",
)

SPECIALIST_DOMAINS: tuple[str, ...] = (
    "fabric",
    "azure-databricks",
    "unity-catalog",
    "synapse",
    "adf",
    "adls",
    "onelake",
    "event-hubs",
    "streaming",
    "purview",
    "entra",
    "networking",
    "finops",
    "spark-performance",
    "delta",
    "iceberg",
    "terraform",
    "bicep",
    "migration",
    "observability",
)
SPECIALIST_IDS: tuple[str, ...] = tuple(f"{d}-specialist" for d in SPECIALIST_DOMAINS)

#: Bounded subagents (section 96) -> parent specialist id.
SUBAGENT_PARENTS: dict[str, str] = {
    "databricks-runtime-reviewer": "azure-databricks-specialist",
    "databricks-uc-reviewer": "azure-databricks-specialist",
    "databricks-performance-reviewer": "azure-databricks-specialist",
    "databricks-cost-reviewer": "azure-databricks-specialist",
}
SUBAGENT_IDS: tuple[str, ...] = tuple(SUBAGENT_PARENTS)

ALL_AGENT_IDS: tuple[str, ...] = ROLE_IDS + SPECIALIST_IDS + SUBAGENT_IDS

CONTEXT_KINDS: tuple[str, ...] = (
    "artifact",
    "code",
    "knowledge",
    "fact",
    "rule",
    "finding",
    "evidence",
    "memory",
    "risk",
    "unresolved",
    "tool_output",
    # eval-plane kinds (evaluation-specialist consumes these, never raw artifacts)
    "eval_result",
    "metric",
    "claim",
)
#: Inputs an agent may declare — the context kinds plus the two entry points
#: (a fresh task, or a handoff arriving from another agent).
INPUT_KINDS: tuple[str, ...] = CONTEXT_KINDS + ("task", "handoff")
#: Artifact kinds an agent may declare as output.
OUTPUT_KINDS: tuple[str, ...] = (
    "fact",
    "evidence",
    "hypothesis",
    "verdict",
    "report",
    "review",
    "recommendations",
    "objections",
    "decision",
    "unresolved",
    "route",
    "handoff",
    "finding",
)
#: When an agent may be spawned (contract v2 `spawn.conditions`).
SPAWN_CONDITIONS: tuple[str, ...] = (
    "always",
    "on_domain_match",
    "on_finding_review",
    "on_disagreement",
    "on_conflict",
    "on_parent_spawn",
    "on_gate",
)
#: Why an agent stops (contract v2 `stop.conditions`).
STOP_CONDITIONS: tuple[str, ...] = (
    "on_artifacts_exhausted",
    "on_unknowns_resolved",
    "on_verdict",
    "on_synthesis_emitted",
    "on_findings_reviewed",
    "on_no_disagreement",
    "on_budget_exhausted",
    "on_eval_complete",
)
#: `review_policy.adversarial_check` values.
ADVERSARIAL_CHECKS: tuple[str, ...] = ("never", "on_conflict", "always")
MODEL_TIERS: tuple[str, ...] = ("economy", "balanced", "deep")
RISKS: tuple[str, ...] = ("read_only", "local_write", "cloud_read")
FORBIDDEN_RISKS: tuple[str, ...] = ("cloud_write",)
#: Mirrors ``sparkforge_azure.agentic.trust.TrustLabel`` values usable as a floor.
TRUST_FLOORS: tuple[str, ...] = (
    "VERIFIED_FINDING",
    "VERIFIED_FACT",
    "KNOWLEDGE",
    "TOOL_OUTPUT",
    "USER_INPUT",
    "EXTERNAL_DATA",
)
HANDOFF_MODE = "DATA_ONLY"
#: The synthesizer may only consume verified findings, evidence and explicit unresolved.
SYNTHESIZER_CONTEXT: frozenset[str] = frozenset({"finding", "evidence", "unresolved"})

BUDGET_KEYS: tuple[str, ...] = (
    "context",
    "tools",
    "model_calls",
    "model_tier",
    "time",
    "handoffs",
)
MAX_CONTEXT_TOKENS_CEILING = 32000
BODY_MIN_LINES = 15
BODY_MAX_LINES = 50
SCHEMA_VERSION = 2
REQUIRED_KEYS: tuple[str, ...] = (
    "schema_version",
    "id",
    "kind",
    "family",
    "domain",
    "role",
    "mission",
    "does",
    "does_not",
    "inputs",
    "outputs",
    "allowed_tools",
    "denied_tools",
    "required_context_kinds",
    "allowed_context_kinds",
    "knowledge_packs",
    "skills",
    "trust_floor",
    "budget",
    "spawn",
    "stop",
    "handoffs",
    "review_policy",
    "evals",
    "agentops_emit_span",
    "risk",
    "parent",
)
#: Optional keys — validated when present, never required. ``rule_areas`` names the
#: rule-id prefixes (``SF-*``) an agent coordinates; consumed by ``case/playbook.py``
#: and ``knowledge_drift.py``, and checked against routing by tests/test_router_agents.py.
OPTIONAL_KEYS: tuple[str, ...] = ("rule_areas",)
_RULE_AREA_RE = re.compile(r"^SF-[A-Z0-9-]+$")
_TOOL_RE = re.compile(r"^sfa_[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class AgentManifest:
    id: str
    kind: str
    data: dict[str, Any]
    body: str
    path: Path

    def list(self, key: str) -> list[str]:
        value = self.data.get(key) or []
        return [str(v) for v in value] if isinstance(value, list) else []

    # ---- contract-v2 accessors (single place key names live) -------------

    @property
    def family(self) -> str:
        return str(self.data.get("family", ""))

    @property
    def domain(self) -> str:
        return str(self.data.get("domain", ""))

    @property
    def mission(self) -> str:
        return str(self.data.get("mission", ""))

    @property
    def allowed_tools(self) -> list[str]:
        return self.list("allowed_tools")

    @property
    def denied_tools(self) -> list[str]:
        return self.list("denied_tools")

    @property
    def allowed_context_kinds(self) -> list[str]:
        return self.list("allowed_context_kinds")

    @property
    def required_context_kinds(self) -> list[str]:
        return self.list("required_context_kinds")

    @property
    def knowledge_packs(self) -> list[str]:
        return self.list("knowledge_packs")

    @property
    def handoffs(self) -> dict[str, Any]:
        value = self.data.get("handoffs")
        return dict(value) if isinstance(value, dict) else {}

    @property
    def handoff_targets(self) -> list[str]:
        targets = self.handoffs.get("allowed_targets")
        return [str(t) for t in targets] if isinstance(targets, list) else []

    @property
    def handoff_mode(self) -> str:
        return str(self.handoffs.get("mode", ""))

    @property
    def spawn(self) -> dict[str, Any]:
        value = self.data.get("spawn")
        return dict(value) if isinstance(value, dict) else {}

    @property
    def stop(self) -> dict[str, Any]:
        value = self.data.get("stop")
        return dict(value) if isinstance(value, dict) else {}

    @property
    def review_policy(self) -> dict[str, Any]:
        value = self.data.get("review_policy")
        return dict(value) if isinstance(value, dict) else {}

    @property
    def evals(self) -> list[str]:
        return self.list("evals")


@dataclass
class ManifestReport:
    errors: list[str] = field(default_factory=list)
    pending_knowledge: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def expected_kind(agent_id: str) -> str | None:
    if agent_id in ROLE_IDS:
        return "role"
    if agent_id in SPECIALIST_IDS:
        return "specialist"
    if agent_id in SUBAGENT_IDS:
        return "subagent"
    return None


def parse_manifest(path: Path) -> AgentManifest:
    _, data, body = split_front_matter(path.read_text(encoding="utf-8"))
    return AgentManifest(
        id=str(data.get("id", "")), kind=str(data.get("kind", "")), data=data, body=body, path=path
    )


def _str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)


def validate_manifest(
    data: dict[str, Any],
    body: str,
    *,
    where: str,
    known_ids: set[str],
    root: Path | None = None,
    allow_pending_knowledge: bool = False,
    file_stem: str | None = None,
) -> ManifestReport:
    """Validate a single manifest. ``known_ids`` is the set of agent ids in the tree."""
    rep = ManifestReport()
    err = rep.errors.append

    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        err(f"{where}: missing keys {missing}")
        return rep
    unknown = sorted(set(data) - set(REQUIRED_KEYS) - set(OPTIONAL_KEYS))
    if unknown:
        err(f"{where}: unknown keys {unknown}")
    if data["schema_version"] != SCHEMA_VERSION:
        err(f"{where}: schema_version must be {SCHEMA_VERSION}")
    if "rule_areas" in data:
        areas = data["rule_areas"]
        if not isinstance(areas, list) or not areas or any(
            not isinstance(a, str) or not _RULE_AREA_RE.match(a) for a in areas
        ):
            err(f"{where}: rule_areas must be a non-empty list of 'SF-*' area prefixes")

    agent_id, kind = data["id"], data["kind"]
    if file_stem is not None and agent_id != file_stem:
        err(f"{where}: id {agent_id!r} differs from file name {file_stem!r}")
    if kind not in KINDS:
        err(f"{where}: kind {kind!r} not in {list(KINDS)}")
    exp = expected_kind(agent_id) if isinstance(agent_id, str) else None
    if exp is None:
        err(f"{where}: id {agent_id!r} is not in the agent taxonomy")
    elif exp != kind:
        err(f"{where}: id {agent_id!r} must have kind {exp!r}")
    family = data["family"]
    if family not in FAMILIES:
        err(f"{where}: family {family!r} not in {list(FAMILIES)}")
    elif kind in FAMILY_BY_KIND and family not in FAMILY_BY_KIND[kind]:
        err(f"{where}: kind {kind!r} cannot have family {family!r}")
    if not isinstance(data["domain"], str) or not data["domain"].strip():
        err(f"{where}: 'domain' must be a non-empty string")
    elif kind == "specialist" and data["domain"] + "-specialist" != agent_id:
        err(f"{where}: specialist domain must derive from id (expected "
            f"{agent_id.removesuffix('-specialist')!r})")
    if not isinstance(data["role"], str) or not data["role"].strip():
        err(f"{where}: 'role' must be a non-empty string")
    if not isinstance(data["mission"], str) or not data["mission"].strip():
        err(f"{where}: 'mission' must be a non-empty string")

    for key in ("does", "does_not", "inputs", "outputs",
                "required_context_kinds", "allowed_context_kinds"):
        if not _str_list(data[key]) or not data[key]:
            err(f"{where}: {key} must be a non-empty list of strings")
    for key in ("allowed_tools", "denied_tools", "skills", "knowledge_packs", "evals"):
        if not _str_list(data[key]):
            err(f"{where}: {key} must be a list of strings")
    if rep.errors:
        return rep

    bad_inputs = sorted(set(data["inputs"]) - set(INPUT_KINDS))
    if bad_inputs:
        err(f"{where}: unknown input kinds {bad_inputs}")
    bad_outputs = sorted(set(data["outputs"]) - set(OUTPUT_KINDS))
    if bad_outputs:
        err(f"{where}: unknown output kinds {bad_outputs}")

    req, allowed = set(data["required_context_kinds"]), set(data["allowed_context_kinds"])
    bad_ctx = sorted((req | allowed) - set(CONTEXT_KINDS))
    if bad_ctx:
        err(f"{where}: unknown context kinds {bad_ctx}")
    if not req <= allowed:
        missing_ctx = sorted(req - allowed)
        err(f"{where}: allowed_context_kinds must include required_context_kinds "
            f"(missing {missing_ctx})")
    if agent_id == "synthesizer" and not allowed <= SYNTHESIZER_CONTEXT:
        err(f"{where}: synthesizer may only use {sorted(SYNTHESIZER_CONTEXT)}")

    for tool in data["allowed_tools"]:
        if not _TOOL_RE.match(tool):
            err(f"{where}: tool {tool!r} must be an 'sfa_*' MCP tool")
    overlap = sorted(set(data["allowed_tools"]) & set(data["denied_tools"]))
    if overlap:
        err(f"{where}: denied_tools wins — tools in both lists {overlap}")
    for tool in data["denied_tools"]:
        if not _TOOL_RE.match(tool):
            err(f"{where}: denied tool {tool!r} must be an 'sfa_*' name")
    for skill in data["skills"]:
        if skill not in SKILL_NAMES:
            err(f"{where}: unknown skill {skill!r}")
    if kind == "specialist" and not data["skills"]:
        err(f"{where}: a specialist must declare at least one skill")
    if agent_id == "coordinator" and data["skills"]:
        err(f"{where}: coordinator routes and never replaces a specialist (no skills)")

    for ref in data["knowledge_packs"]:
        kerr = validate_knowledge_ref(ref)
        if kerr:
            err(f"{where}: {kerr}")
        elif root is not None and not knowledge_ref_exists(root, ref):
            if allow_pending_knowledge:
                rep.pending_knowledge.append(ref)
            else:
                err(f"{where}: knowledge dir {ref!r} does not exist")

    budget = data["budget"]
    if not isinstance(budget, dict) or sorted(budget) != sorted(BUDGET_KEYS):
        err(f"{where}: budget must have exactly {list(BUDGET_KEYS)}")
    else:
        for key in ("context", "tools", "model_calls", "time", "handoffs"):
            val = budget[key]
            if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
                err(f"{where}: budget.{key} must be a positive integer")
        mct = budget["context"]
        if isinstance(mct, int) and mct > MAX_CONTEXT_TOKENS_CEILING:
            err(f"{where}: budget.context exceeds {MAX_CONTEXT_TOKENS_CEILING}")
        if budget["model_tier"] not in MODEL_TIERS:
            err(f"{where}: budget.model_tier must be one of {list(MODEL_TIERS)}")

    spawn = data["spawn"]
    if not isinstance(spawn, dict) or not _str_list(spawn.get("conditions")):
        err(f"{where}: spawn.conditions must be a non-empty list of strings")
    else:
        bad_spawn = sorted(set(spawn["conditions"]) - set(SPAWN_CONDITIONS))
        if bad_spawn:
            err(f"{where}: unknown spawn conditions {bad_spawn}")
        gain = spawn.get("information_gain_threshold")
        if isinstance(gain, bool) or not isinstance(gain, (int, float)) or gain < 0:
            err(f"{where}: spawn.information_gain_threshold must be a number >= 0")
    stop = data["stop"]
    if not isinstance(stop, dict) or not _str_list(stop.get("conditions")):
        err(f"{where}: stop.conditions must be a non-empty list of strings")
    else:
        bad_stop = sorted(set(stop["conditions"]) - set(STOP_CONDITIONS))
        if bad_stop:
            err(f"{where}: unknown stop conditions {bad_stop}")

    handoffs = data["handoffs"]
    if not isinstance(handoffs, dict) or not _str_list(handoffs.get("allowed_targets")):
        err(f"{where}: handoffs.allowed_targets must be a non-empty list of strings")
    else:
        targets = handoffs["allowed_targets"]
        resolvable = known_ids | set(ROLE_IDS)
        for target in targets:
            if target not in resolvable:
                err(f"{where}: handoff target {target!r} does not resolve to an agent or role")
            if target == agent_id:
                err(f"{where}: agent cannot hand off to itself")
        if handoffs.get("mode") != HANDOFF_MODE:
            err(f"{where}: handoffs.mode must be {HANDOFF_MODE}")

    policy = data["review_policy"]
    if not isinstance(policy, dict):
        err(f"{where}: review_policy must be a mapping")
    else:
        if not isinstance(policy.get("requires_verifier"), bool):
            err(f"{where}: review_policy.requires_verifier must be a bool")
        if policy.get("adversarial_check") not in ADVERSARIAL_CHECKS:
            err(f"{where}: review_policy.adversarial_check must be one of "
                f"{list(ADVERSARIAL_CHECKS)}")
    if not isinstance(data["agentops_emit_span"], bool):
        err(f"{where}: agentops_emit_span must be a bool")

    risk = data["risk"]
    if risk in FORBIDDEN_RISKS:
        err(f"{where}: risk {risk!r} is forbidden (agents never write to the cloud)")
    elif risk not in RISKS:
        err(f"{where}: risk {risk!r} not in {list(RISKS)}")
    if data["trust_floor"] not in TRUST_FLOORS:
        err(f"{where}: trust_floor {data['trust_floor']!r} not in {list(TRUST_FLOORS)}")

    parent = data["parent"]
    if kind == "subagent":
        if not parent:
            err(f"{where}: a subagent must declare a parent")
        elif parent not in known_ids or expected_kind(parent) != "specialist":
            err(f"{where}: parent {parent!r} must be an existing specialist")
        elif SUBAGENT_PARENTS.get(agent_id) not in (None, parent):
            err(f"{where}: parent must be {SUBAGENT_PARENTS[agent_id]!r}")
    elif parent is not None:
        err(f"{where}: only subagents may declare a parent")

    n = body_line_count(body)
    if not BODY_MIN_LINES <= n <= BODY_MAX_LINES:
        err(f"{where}: body has {n} lines (expected {BODY_MIN_LINES}-{BODY_MAX_LINES})")
    if agent_id == "coordinator":
        missing_routes = [s for s in SPECIALIST_IDS if s not in body]
        if missing_routes:
            err(f"{where}: routing table does not mention {missing_routes}")
    return rep


def agents_dir(root: Path) -> Path:
    return root / "agents"


def discover_manifests(root: Path) -> list[Path]:
    base = agents_dir(root)
    if not base.is_dir():
        return []
    return sorted(p for p in base.glob("*.md") if p.name.lower() != "readme.md")


def load_manifests(root: Path) -> list[AgentManifest]:
    return [parse_manifest(p) for p in discover_manifests(root)]


def validate_agents_tree(root: Path, *, allow_pending_knowledge: bool = False) -> ManifestReport:
    """Validate the full taxonomy (14 roles + 20 specialists + 4 subagents) and each manifest."""
    rep = ManifestReport()
    paths = discover_manifests(root)
    parsed: list[tuple[Path, dict[str, Any], str]] = []
    for path in paths:
        try:
            _, data, body = split_front_matter(path.read_text(encoding="utf-8"))
        except (OSError, FrontMatterError) as exc:
            rep.errors.append(f"{rel_label(path, root)}: {exc}")
            continue
        parsed.append((path, data, body))
    known = {str(d.get("id")) for _, d, _ in parsed}
    stems = {p.stem for p in paths}
    missing = [a for a in ALL_AGENT_IDS if a not in stems]
    extra = sorted(stems - set(ALL_AGENT_IDS))
    if missing:
        rep.errors.append(f"agents: missing {missing}")
    if extra:
        rep.errors.append(f"agents: unexpected {extra}")
    for path, data, body in parsed:
        sub = validate_manifest(
            data,
            body,
            where=rel_label(path, root),
            known_ids=known,
            root=root,
            allow_pending_knowledge=allow_pending_knowledge,
            file_stem=path.stem,
        )
        rep.errors.extend(sub.errors)
        rep.pending_knowledge.extend(sub.pending_knowledge)
    rep.pending_knowledge = sorted(set(rep.pending_knowledge))
    return rep
