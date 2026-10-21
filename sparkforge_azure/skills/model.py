"""SKILL.md contract v1 (sections 156-159): parse and validate skill front matter.

Single source of truth lives in ``skills/<name>/SKILL.md`` at the repository root. This module
is deterministic and offline: it never calls a model, never touches the network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONTRACT_VERSION = "v1"

#: The exact skill catalogue (section 156). Order is canonical and used for listings.
SKILL_NAMES: tuple[str, ...] = (
    "azure-spark",
    "azure-databricks",
    "unity-catalog",
    "fabric-data-engineering",
    "fabric-onelake",
    "fabric-realtime",
    "azure-synapse",
    "azure-data-factory",
    "azure-adls",
    "azure-event-hubs",
    "azure-purview",
    "azure-entra",
    "azure-networking",
    "azure-finops",
    "delta-lake",
    "iceberg",
    "spark-performance",
    "spark-streaming",
    "analyze-batch-loop",
    "azure-terraform",
    "azure-bicep",
    "azure-observability",
    "delegate-specialists",
)

SOURCE_AUTHORITIES: tuple[str, ...] = (
    "microsoft_official",
    "databricks_official",
    "apache_spark_official",
    "delta_io_official",
    "apache_iceberg_official",
    "hashicorp_official",
    "finops_foundation",
    "forge_lab_evidence",
)

#: Knowledge domains (directory refs). ``knowledge/azure/`` refs must name a known sub-domain.
KNOWLEDGE_TOP_DOMAINS: tuple[str, ...] = (
    "spark",
    "lakehouse",
    "azure",
    "governance",
    "migration",
    "data-quality",
    "agentic",
)
KNOWLEDGE_AZURE_DOMAINS: tuple[str, ...] = (
    "databricks",
    "unity-catalog",
    "fabric",
    "synapse",
    "adf",
    "storage",
    "eventhubs",
    "purview",
    "identity",
    "network",
    "finops",
    "observability",
    "iac",
)

#: Planned CLI verbs (``sparkforge-azure <verb> [<sub>]``). ``None`` = free-form argument
#: (e.g. ``analyze <kind>``); a tuple = closed set of sub-verbs; empty tuple = no sub-verb.
CLI_NAME = "sparkforge-azure"
CLI_VERBS: dict[str, tuple[str, ...] | None] = {
    "analyze": None,
    "judge": (),
    "governance": ("diagnose",),
    "graph": ("build", "query", "impact"),
    "tokensave": ("search", "read", "symbols", "refs", "diff", "expand", "context"),
    "knowledge": ("select", "check"),
    "doctor": (),
    "lab": ("run", "verify", "describe", "scenarios"),
    "collect": ("workspace-graph", "unity-catalog", "adls-meta", "azure-rbac"),
    "diagnose": ("", "fabric", "stream"),  # "" = access vertical (diagnose --bundle)
    "migration": ("assess",),
    "offline-bundle": (),
    "agentops": ("inspect", "waste"),
    "delegate": ("discover", "plan", "run", "handoffs"),
}
MCP_TOOL_RE = re.compile(r"^sfa_[a-z][a-z0-9_]*$")
_KIND_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

DESCRIPTION_MAX = 600
BODY_MIN_LINES = 40
BODY_MAX_LINES = 120
REQUIRED_LIST_FIELDS: tuple[str, ...] = (
    "trigger",
    "scope",
    "does",
    "does_not",
    "knowledge_refs",
    "tool_refs",
    "eval_refs",
    "source_authority",
)
#: Verbs a skill targets but the CLI does not implement yet. Never in the body.
OPTIONAL_LIST_FIELDS: tuple[str, ...] = ("planned_tool_refs",)
REQUIRED_BODY_HEADINGS: tuple[str, ...] = (
    "## Procedimento",
    "## Pontos de decisão",
    "## Não concluir sem evidência",
    "## Handoff",
)
EVAL_CASE_KEYS: tuple[str, ...] = (
    "id",
    "prompt",
    "must_include",
    "must_not_include",
    "expected_tools",
)
MIN_EVAL_CASES = 3
EVAL_KINDS: frozenset[str] = frozenset({"positive", "negative", "boundary"})
# Skills verticais (access UC/ADLS + Fabric + Streaming/RTI, cycles 2–4):
# exigem evals com trigger positivo, trigger negativo e caso de fronteira.
VERTICAL_SKILLS: frozenset[str] = frozenset({
    "azure-adls",
    "azure-data-factory",
    "azure-databricks",
    "azure-entra",
    "azure-event-hubs",
    "azure-networking",
    "delta-lake",
    "fabric-data-engineering",
    "fabric-onelake",
    "fabric-realtime",
    "azure-synapse",
    "spark-performance",
    "spark-streaming",
    "unity-catalog",
})

_FRONT_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)


class FrontMatterError(ValueError):
    """Raised when a markdown document has no parseable YAML front matter."""


def split_front_matter(text: str) -> tuple[str, dict[str, Any], str]:
    """Return ``(raw_yaml, data, body)``. Raises :class:`FrontMatterError`."""
    match = _FRONT_RE.match(text)
    if not match:
        raise FrontMatterError("missing YAML front matter delimited by '---'")
    raw, body = match.group(1), match.group(2)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:  # pragma: no cover - message passthrough
        raise FrontMatterError(f"invalid YAML front matter: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontMatterError("front matter must be a mapping")
    return raw, data, body


def rel_label(path: Path, root: Path | None) -> str:
    """Repository-relative posix label for error messages (absolute if outside ``root``)."""
    if root is not None:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return path.as_posix()


def body_line_count(body: str) -> int:
    return len(body.strip("\n").splitlines())


def validate_knowledge_ref(ref: Any) -> str | None:
    """Return an error string for a malformed knowledge directory ref, else ``None``."""
    if not isinstance(ref, str) or not ref.startswith("knowledge/") or not ref.endswith("/"):
        return f"knowledge ref {ref!r} must be a directory path 'knowledge/<domain>/'"
    parts = ref.strip("/").split("/")
    if len(parts) < 2 or parts[1] not in KNOWLEDGE_TOP_DOMAINS:
        return f"knowledge ref {ref!r} uses unknown domain"
    if parts[1] == "azure" and (len(parts) < 3 or parts[2] not in KNOWLEDGE_AZURE_DOMAINS):
        return f"knowledge ref {ref!r} must name a known azure sub-domain"
    if any(p in ("", ".", "..") for p in parts):
        return f"knowledge ref {ref!r} has an invalid path segment"
    return None


def knowledge_ref_exists(root: Path, ref: str) -> bool:
    return (root / ref).is_dir()


def validate_tool_ref(ref: Any) -> str | None:
    """A tool ref is either an ``sfa_*`` MCP tool or a planned ``sparkforge-azure`` verb."""
    if not isinstance(ref, str):
        return f"tool ref {ref!r} must be a string"
    if MCP_TOOL_RE.match(ref):
        return None
    words = ref.split()
    if not words or words[0] != CLI_NAME:
        return f"tool ref {ref!r} must be 'sfa_*' or start with '{CLI_NAME} '"
    if len(words) < 2 or words[1] not in CLI_VERBS:
        return f"tool ref {ref!r} uses an unknown CLI verb"
    subs = CLI_VERBS[words[1]]
    rest = words[2:]
    if subs is None:
        if len(rest) != 1 or not _KIND_RE.match(rest[0]):
            return f"tool ref {ref!r}: '{words[1]}' requires exactly one <kind> argument"
    elif not subs:
        if rest:
            return f"tool ref {ref!r}: '{words[1]}' takes no sub-verb"
    elif not rest and "" in subs:
        return None
    elif len(rest) != 1 or rest[0] not in subs:
        return f"tool ref {ref!r}: '{words[1]}' sub-verb must be one of {list(subs)}"
    return None


def real_cli_paths(root: Path) -> frozenset[str] | None:
    """Implemented CLI command paths from the surface lock (``docs/surface.lock.json``).

    Read from the lock, not the parser: skills must not import the CLI layer.
    Falls back to the checkout holding this package; ``None`` when no lock is
    reachable (installed wheel), which skips the existence check.
    """
    import json

    for base in (root, Path(__file__).resolve().parents[2]):
        lock = base / "docs" / "surface.lock.json"
        if lock.is_file():
            commands = json.loads(lock.read_text(encoding="utf-8"))["cli"]["commands"]
            return frozenset(commands)
    return None


def cli_ref_resolves(ref: str, paths: frozenset[str]) -> bool:
    """``sparkforge-azure <verb> [<sub>]`` names an implemented command (or group)."""
    if not ref.startswith(f"{CLI_NAME} "):
        return True  # sfa_* refs are checked by the agent tool registry
    cmd = ref.removeprefix(f"{CLI_NAME} ").strip()
    return cmd in paths or any(p.startswith(cmd + " ") for p in paths)


_BODY_CLI_RE = re.compile(rf"(?<![\w./-]){CLI_NAME} ([a-z][a-z0-9-]*)(?: ([a-z][a-z0-9-]*))?")


def body_cli_refs(body: str) -> list[str]:
    """Normalised ``sparkforge-azure <verb> [<sub>]`` refs used in a skill body."""
    refs: list[str] = []
    for verb, nxt in _BODY_CLI_RE.findall(body):
        subs = CLI_VERBS.get(verb, ())
        if subs is None or (subs and nxt in subs):
            ref = f"{CLI_NAME} {verb} {nxt}".strip()
        else:
            ref = f"{CLI_NAME} {verb}"
        if ref not in refs:
            refs.append(ref)
    return refs


_HANDOFF_BULLET_RE = re.compile(r"^-\s+(.*)$", re.MULTILINE)
_HANDOFF_TICK_RE = re.compile(r"`([a-z][a-z0-9-]*)`")


def body_handoff_refs(body: str) -> list[str]:
    """Backticked targets listed as bullets under the ``## Handoff`` section."""
    _, sep, tail = body.partition("## Handoff")
    if not sep:
        return []
    tail = re.split(r"\n## ", tail, maxsplit=1)[0]
    refs: list[str] = []
    for line in _HANDOFF_BULLET_RE.findall(tail):
        refs.extend(_HANDOFF_TICK_RE.findall(line))
    return refs


def _handoff_targets() -> frozenset[str]:
    """Closed set of valid handoff targets: skills ∪ taxonomy agents.

    Lazy import: ``agentmanifest.model`` already imports this module, so a
    top-level import would be circular.
    """
    from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS

    return frozenset(SKILL_NAMES) | frozenset(ALL_AGENT_IDS)


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    metadata: dict[str, Any]
    body: str
    path: Path

    def meta_list(self, key: str) -> list[str]:
        value = self.metadata.get(key) or []
        return [str(v) for v in value] if isinstance(value, list) else []

    @property
    def trigger(self) -> list[str]:
        return self.meta_list("trigger")

    @property
    def scope(self) -> list[str]:
        return self.meta_list("scope")

    @property
    def knowledge_refs(self) -> list[str]:
        return self.meta_list("knowledge_refs")

    @property
    def tool_refs(self) -> list[str]:
        return self.meta_list("tool_refs")

    @property
    def eval_refs(self) -> list[str]:
        return self.meta_list("eval_refs")


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    pending_knowledge: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: ValidationReport) -> None:
        self.errors.extend(other.errors)
        self.pending_knowledge.extend(other.pending_knowledge)


def parse_skill(path: Path) -> Skill:
    _, data, body = split_front_matter(path.read_text(encoding="utf-8"))
    metadata = data.get("metadata")
    return Skill(
        name=str(data.get("name", "")),
        description=str(data.get("description", "")),
        metadata=metadata if isinstance(metadata, dict) else {},
        body=body,
        path=path,
    )


def validate_skill_file(
    path: Path, root: Path, *, allow_pending_knowledge: bool = False
) -> ValidationReport:
    """Validate one ``skills/<name>/SKILL.md`` against contract v1."""
    rep = ValidationReport()
    where = rel_label(path, root)
    try:
        _, data, body = split_front_matter(path.read_text(encoding="utf-8"))
    except (OSError, FrontMatterError) as exc:
        rep.errors.append(f"{where}: {exc}")
        return rep

    name = data.get("name")
    dir_name = path.parent.name
    if not isinstance(name, str) or not _NAME_RE.match(name):
        rep.errors.append(f"{where}: 'name' must be a kebab-case string")
        name = dir_name
    if name != dir_name:
        rep.errors.append(f"{where}: name {name!r} differs from directory {dir_name!r}")
    if name not in SKILL_NAMES:
        rep.errors.append(f"{where}: {name!r} is not in the skill catalogue")

    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.errors.append(f"{where}: 'description' is required")
    elif len(desc) > DESCRIPTION_MAX:
        rep.errors.append(f"{where}: description has {len(desc)} chars (max {DESCRIPTION_MAX})")

    meta = data.get("metadata")
    if not isinstance(meta, dict):
        rep.errors.append(f"{where}: 'metadata' mapping is required")
        return rep
    if meta.get("sparkforge_azure_contract") != CONTRACT_VERSION:
        rep.errors.append(f"{where}: metadata.sparkforge_azure_contract must be {CONTRACT_VERSION}")
    unknown = sorted(set(meta) - set(REQUIRED_LIST_FIELDS) - set(OPTIONAL_LIST_FIELDS)
                    - {"sparkforge_azure_contract"})
    if unknown:
        rep.errors.append(f"{where}: unknown metadata keys {unknown}")
    for key in REQUIRED_LIST_FIELDS:
        value = meta.get(key)
        if not isinstance(value, list) or not value:
            rep.errors.append(f"{where}: metadata.{key} must be a non-empty list")
        elif any(not isinstance(v, str) or not v.strip() for v in value):
            rep.errors.append(f"{where}: metadata.{key} items must be non-empty strings")
        elif len(set(value)) != len(value):
            rep.errors.append(f"{where}: metadata.{key} has duplicates")

    for ref in meta.get("knowledge_refs") or []:
        err = validate_knowledge_ref(ref)
        if err:
            rep.errors.append(f"{where}: {err}")
        elif not knowledge_ref_exists(root, ref):
            if allow_pending_knowledge:
                rep.pending_knowledge.append(ref)
            else:
                rep.errors.append(f"{where}: knowledge dir {ref!r} does not exist")
    cli_paths = real_cli_paths(root)
    for ref in meta.get("tool_refs") or []:
        err = validate_tool_ref(ref)
        if err:
            rep.errors.append(f"{where}: {err}")
        elif cli_paths is not None and not cli_ref_resolves(ref, cli_paths):
            rep.errors.append(
                f"{where}: tool_ref {ref!r} is not a real CLI command; "
                "declare it in planned_tool_refs and keep it out of the body"
            )
    planned = meta.get("planned_tool_refs") or []
    if not isinstance(planned, list):
        rep.errors.append(f"{where}: metadata.planned_tool_refs must be a list")
        planned = []
    for ref in planned:
        err = validate_tool_ref(ref)
        if err:
            rep.errors.append(f"{where}: planned: {err}")
        elif cli_paths is not None and cli_ref_resolves(ref, cli_paths):
            rep.errors.append(f"{where}: planned_tool_ref {ref!r} already exists; "
                              "move it to tool_refs")
        elif ref in body:
            rep.errors.append(f"{where}: body instructs planned verb {ref!r} as if it existed")
    for src in meta.get("source_authority") or []:
        if src not in SOURCE_AUTHORITIES:
            rep.errors.append(f"{where}: unknown source_authority {src!r}")

    expected_eval = f"skills/{dir_name}/evals/evals.yaml"
    evals = meta.get("eval_refs") or []
    if expected_eval not in evals:
        rep.errors.append(f"{where}: eval_refs must include {expected_eval}")
    for ref in evals:
        if isinstance(ref, str):
            eval_path = root / ref
            if not eval_path.is_file():
                rep.errors.append(f"{where}: eval file {ref!r} does not exist")
            else:
                rep.extend(
                    validate_evals_file(eval_path, skill_name=name, tool_refs=meta.get("tool_refs"),
                                        skill_text=body, root=root)
                )

    n = body_line_count(body)
    if not BODY_MIN_LINES <= n <= BODY_MAX_LINES:
        bounds = f"{BODY_MIN_LINES}-{BODY_MAX_LINES}"
        rep.errors.append(f"{where}: body has {n} lines (expected {bounds})")
    for heading in REQUIRED_BODY_HEADINGS:
        if heading not in body:
            rep.errors.append(f"{where}: body is missing heading {heading!r}")
    declared = set(meta.get("tool_refs") or [])
    for ref in body_cli_refs(body):
        err = validate_tool_ref(ref)
        if err:
            rep.errors.append(f"{where}: body uses invalid CLI ref: {err}")
        elif ref not in declared:
            rep.errors.append(f"{where}: body uses {ref!r} but it is not declared in tool_refs")
    if re.search(r"(?<![\w-])sparkforge (?!-)", body):
        rep.errors.append(f"{where}: body references the AWS CLI 'sparkforge'; use '{CLI_NAME}'")
    valid_targets = _handoff_targets()
    for target in body_handoff_refs(body):
        if target not in valid_targets:
            rep.errors.append(
                f"{where}: handoff target {target!r} is not a skill or a taxonomy agent"
            )
    return rep


def validate_evals_file(
    path: Path,
    *,
    skill_name: str,
    tool_refs: Any = None,
    skill_text: str | None = None,
    root: Path | None = None,
) -> ValidationReport:
    """Validate the statically checkable eval suite of a skill.

    * ``skill`` equals the owning skill; at least :data:`MIN_EVAL_CASES` cases;
    * each case has the five keys, unique ``id``, non-empty lists;
    * ``expected_tools`` must be a subset of the skill's ``tool_refs``;
    * ``must_include`` terms must be grounded in the skill body (case-insensitive) and be
      disjoint from ``must_not_include``.
    """
    rep = ValidationReport()
    where = rel_label(path, root)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        rep.errors.append(f"{where}: cannot parse evals: {exc}")
        return rep
    if not isinstance(data, dict):
        rep.errors.append(f"{where}: evals root must be a mapping")
        return rep
    if data.get("skill") != skill_name:
        rep.errors.append(f"{where}: 'skill' must be {skill_name!r}")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < MIN_EVAL_CASES:
        rep.errors.append(f"{where}: needs at least {MIN_EVAL_CASES} cases")
        return rep
    tools = set(tool_refs or [])
    lowered = (skill_text or "").lower()
    seen: set[str] = set()
    kinds: set[str] = set()
    for i, case in enumerate(cases):
        label = f"{where}[{i}]"
        if not isinstance(case, dict):
            rep.errors.append(f"{label}: case must be a mapping")
            continue
        missing = [k for k in EVAL_CASE_KEYS if k not in case]
        if missing:
            rep.errors.append(f"{label}: missing keys {missing}")
            continue
        cid = case["id"]
        if not isinstance(cid, str) or not cid:
            rep.errors.append(f"{label}: id must be a non-empty string")
        elif cid in seen:
            rep.errors.append(f"{label}: duplicate id {cid!r}")
        else:
            seen.add(cid)
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            rep.errors.append(f"{label}: prompt must be a non-empty string")
        kind = case.get("kind", "positive")
        if kind not in EVAL_KINDS:
            rep.errors.append(
                f"{label}: kind {kind!r} invalid (use {sorted(EVAL_KINDS)})")
        else:
            kinds.add(kind)
        bad_lists = False
        for key in ("must_include", "must_not_include", "expected_tools"):
            val = case[key]
            if not isinstance(val, list) or not val or not all(isinstance(v, str) for v in val):
                rep.errors.append(f"{label}: {key} must be a non-empty list of strings")
                bad_lists = True
        if bad_lists:
            continue
        overlap = {v.lower() for v in case["must_include"]} & {
            v.lower() for v in case["must_not_include"]
        }
        if overlap:
            rep.errors.append(
                f"{label}: must_include and must_not_include overlap {sorted(overlap)}"
            )
        if tool_refs is not None:
            extra = [t for t in case["expected_tools"] if t not in tools]
            if extra:
                rep.errors.append(f"{label}: expected_tools not in skill tool_refs: {extra}")
        if skill_text is not None:
            ungrounded = [t for t in case["must_include"] if t.lower() not in lowered]
            if ungrounded:
                rep.errors.append(
                    f"{label}: must_include terms not grounded in SKILL.md: {ungrounded}"
                )
    if skill_name in VERTICAL_SKILLS:
        missing_kinds = {"negative", "boundary"} - kinds
        if missing_kinds:
            rep.errors.append(
                f"{where}: vertical skill needs eval kinds {sorted(missing_kinds)} "
                "(positive trigger + negative trigger + boundary)"
            )
    return rep


def skills_dir(root: Path) -> Path:
    return root / "skills"


def discover_skill_files(root: Path) -> list[Path]:
    base = skills_dir(root)
    if not base.is_dir():
        return []
    return sorted(
        p / "SKILL.md" for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )


def validate_skills_tree(root: Path, *, allow_pending_knowledge: bool = False) -> ValidationReport:
    """Validate every skill and the catalogue itself (exactly :data:`SKILL_NAMES`)."""
    rep = ValidationReport()
    files = discover_skill_files(root)
    found = {p.parent.name for p in files}
    missing = [n for n in SKILL_NAMES if n not in found]
    extra = sorted(found - set(SKILL_NAMES))
    if missing:
        rep.errors.append(f"skills: missing {missing}")
    if extra:
        rep.errors.append(f"skills: unexpected {extra}")
    base = skills_dir(root)
    if base.is_dir():
        for d in sorted(base.iterdir()):
            if d.is_dir() and not (d / "SKILL.md").is_file() and not d.name.startswith(("_", ".")):
                rep.errors.append(f"skills: directory {d.name!r} has no SKILL.md")
    for path in files:
        rep.extend(validate_skill_file(path, root, allow_pending_knowledge=allow_pending_knowledge))
    rep.pending_knowledge = sorted(set(rep.pending_knowledge))
    return rep
