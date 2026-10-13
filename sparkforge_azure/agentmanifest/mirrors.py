"""Host mirrors of the agent manifests (section 142).

``agents/<id>.md`` is the only editable copy. Mirrors are rendered
deterministically for each agent host under a ``sparkforge-azure-`` prefix —
file-per-agent, since hosts conventionally scan ``<root>/*.md``. Host
frontmatter requires ``name``/``description``; the render injects both from
``id``/``mission`` (plus routing terms for specialists) and a read-only
``tools`` list, while the rest of the manifest is preserved verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS
from sparkforge_azure.skills.model import split_front_matter

MIRROR_PREFIX = "sparkforge-azure-"
#: Host mirror roots, relative to the repository root.
AGENT_MIRROR_ROOTS: tuple[str, ...] = (".claude/agents/custom", ".agents/agents")


def mirror_name(agent_id: str) -> str:
    return f"{MIRROR_PREFIX}{agent_id}"


def generated_header(agent_id: str) -> str:
    return f"<!-- GENERATED from agents/{agent_id}.md; do not edit -->"


#: Host tools every agent mirror gets: reading only. No Write/Edit/Web/Agent —
#: manifests are ``risk: read_only`` and a host without ``tools:`` grants all.
HOST_READ_TOOLS: tuple[str, ...] = ("Read", "Grep", "Glob")


def host_tools(allowed_tools: list[str]) -> list[str]:
    """Host tool list: read tools, plus Bash when the manifest declares any
    ``sfa_*`` tool (each one has an equivalent ``sparkforge-azure`` verb and no
    MCP server is registered for the host)."""
    tools = list(HOST_READ_TOOLS)
    if any(str(t).startswith("sfa_") for t in allowed_tools):
        tools.append("Bash")
    return tools


def host_description(agent_id: str, mission: str) -> str:
    """Mission plus, for specialists, when to delegate (routing-table terms)."""
    from sparkforge_azure.agentmanifest.routing import ROUTING_TABLE

    row = next((r for r in ROUTING_TABLE if r.specialist == agent_id), None)
    if row is None:
        return mission
    return f"{mission} Use quando a tarefa envolve: {', '.join(row.terms[:8])}."


def render_agent_mirror(source_text: str, agent_id: str) -> str:
    """Render the host mirror: frontmatter gains ``name``/``description``.

    The YAML mapping is re-serialized deterministically (``sort_keys=False``
    keeps the source order; injected keys go last). The body is preserved
    verbatim and line endings are normalised to ``\\n``.
    """
    text = source_text.replace("\r\n", "\n")
    _, data, body = split_front_matter(text)
    if data.get("id") != agent_id:
        raise ValueError(f"source id {data.get('id')!r} != {agent_id!r}")
    data["name"] = mirror_name(agent_id)
    data["description"] = host_description(agent_id, str(data.get("mission", "")).strip())
    data["tools"] = ", ".join(host_tools(data.get("allowed_tools") or []))
    new_raw = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    return (
        f"---\n{new_raw}---\n"
        f"{generated_header(agent_id)}\n{body.lstrip(chr(10))}"
    )


@dataclass(frozen=True)
class MirrorDrift:
    path: str
    reason: str  # missing | stale | orphan


def expected_agent_mirrors(root: Path) -> dict[Path, str]:
    out: dict[Path, str] = {}
    for agent_id in ALL_AGENT_IDS:
        src = root / "agents" / f"{agent_id}.md"
        if not src.is_file():
            continue
        text = render_agent_mirror(src.read_text(encoding="utf-8"), agent_id)
        for mroot in AGENT_MIRROR_ROOTS:
            out[root / mroot / f"{mirror_name(agent_id)}.md"] = text
    return out


def _agent_orphans(root: Path, expected: dict[Path, str]) -> list[Path]:
    out: list[Path] = []
    for mroot in AGENT_MIRROR_ROOTS:
        base = root / mroot
        if base.is_dir():
            for f in sorted(base.iterdir()):
                ours = (
                    f.is_file()
                    and f.name.startswith(MIRROR_PREFIX)
                    and f.suffix == ".md"
                )
                if ours and f not in expected:
                    out.append(f)
    return out


def check_agent_mirrors(root: Path) -> list[MirrorDrift]:
    """Return drift between sources and mirrors (empty list = in sync)."""
    root = Path(root)
    drift: list[MirrorDrift] = []
    expected = expected_agent_mirrors(root)
    for path, text in sorted(expected.items()):
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            drift.append(MirrorDrift(rel, "missing"))
        elif path.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            drift.append(MirrorDrift(rel, "stale"))
    for f in _agent_orphans(root, expected):
        drift.append(MirrorDrift(f.relative_to(root).as_posix(), "orphan"))
    return drift


def sync_agent_mirrors(root: Path) -> list[str]:
    """Write all mirrors and delete orphaned ``sparkforge-azure-*`` mirrors."""
    root = Path(root)
    changed: list[str] = []
    expected = expected_agent_mirrors(root)
    for path, text in sorted(expected.items()):
        current = (
            path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if path.is_file()
            else None
        )
        if current != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
            changed.append(path.relative_to(root).as_posix())
    for f in _agent_orphans(root, expected):
        f.unlink()
        changed.append(f.relative_to(root).as_posix())
    return changed
