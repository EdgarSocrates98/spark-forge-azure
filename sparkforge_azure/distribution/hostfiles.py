"""Host-facing project files (P0-E — §65–§79).

What ``distribution init`` writes so hosts pick the project up:

- ``.mcp.json`` managed key — done in ``service.initialize`` (MCP clients,
  Claude Code, Codex and Devin all read it).
- A **managed marker block** in ``AGENTS.md`` (always — the generic agent
  contract that Codex and Devin load natively) and in ``CLAUDE.md`` when the
  file exists or the ``claude`` host was detected. The block is delimited,
  so it coexists with user content and detaches cleanly (§70–§71).
- ``--with-mirrors`` materializes the agent catalog into the conventional
  host roots — ``.claude/agents/custom/`` and ``.agents/agents/`` — rendered
  by the same ``agentmanifest.mirrors`` generator the repo uses, from the
  packaged ``agents/`` sources (source checkout or ``_data/`` wheel; §66).

Hosts are detected, never probed live (§76–§77): detection only steers
which optional files appear; nothing fails on an absent host.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from sparkforge_azure.agentmanifest.mirrors import (
    AGENT_MIRROR_ROOTS,
    mirror_name,
    render_agent_mirror,
)
from sparkforge_azure.distribution.assets import _group_dir
from sparkforge_azure.distribution.managed import (
    apply_marker_block,
    marker_block_sha,
    record_file,
    write_managed_file,
)

_BLOCK_BODY = """\
**Spark Forge Azure** integration is active in this project.

- MCP server: `sparkforge-azure mcp serve` (managed key in `.mcp.json`)
- Lifecycle: `sparkforge-azure distribution status|doctor|detach`
- Agents mirror (opt-in): `sparkforge-azure distribution init --with-mirrors`

Everything between the `sparkforge-azure` markers is managed; edits outside
the markers are yours and are never overwritten."""


def agents_marker_block() -> str:
    return _BLOCK_BODY


def _agent_sources() -> list[tuple[str, str]]:
    """(agent_id, source_text) from the canonical `agents/` assets."""
    root = _group_dir("agents")
    if not root.is_dir():
        return []
    out: list[tuple[str, str]] = []
    for item in sorted(root.iterdir(), key=lambda e: e.name):
        if item.is_file() and item.suffix == ".md":
            try:
                out.append((item.stem, item.read_text(encoding="utf-8")))
            except (OSError, UnicodeError):
                continue
    return out


#: Which selected hosts each agent-mirror root serves (install-2.1). A
#: root is written when ANY of its hosts is selected — `.agents/agents` is
#: the shared Devin/Codex/Copilot surface, `.claude/agents/custom` is
#: Claude-only.
_AGENT_ROOT_HOSTS: dict[str, tuple[str, ...]] = {
    ".claude/agents/custom": ("claude",),
    ".agents/agents": ("devin", "codex", "copilot"),
}


def install_host_assets(
    root: Path,
    ledger: dict[str, Any],
    *,
    hosts: tuple[str, ...] = (),
    with_mirrors: bool = False,
    write_markers: bool = True,
    enabled_kinds: set[str] | None = None,
    mirror_hosts: tuple[str, ...] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write the host-facing files; returns (ledger, report).

    ``write_markers=False`` skips the legacy ``sparkforge-azure`` marker
    blocks — the ``forge:*`` consumer-docs layer (forge_context) owns
    AGENTS.md/CLAUDE.md on the install path (lf-0036).

    ``hosts`` steers detection-based choices (``CLAUDE.md`` only for
    claude); ``mirror_hosts`` scopes the agent-mirror roots the install
    selected via ``--host`` (install-2.1) — ``None`` keeps the legacy
    bulk behavior (every declared root, used by ``distribution init``).
    ``enabled_kinds`` narrows by asset kind (``agent``/``marker``) —
    ``None`` means no narrowing."""
    agent_roots = (
        list(AGENT_MIRROR_ROOTS)
        if mirror_hosts is None
        else [
            r for r in AGENT_MIRROR_ROOTS
            if set(mirror_hosts) & set(_AGENT_ROOT_HOSTS.get(r, ()))
        ]
    )
    report: dict[str, Any] = {
        "marker_files": [],
        "mirrors": {
            "written": 0, "unchanged": 0,
            # Payload bytes rendered / really written — measured bytes,
            # never tokens (cycle 16.1 §7.4, context honesty §8.5).
            "bytes": 0, "written_bytes": 0,
            "roots": agent_roots,
        },
        "skipped": [],
        "preserved_foreign": [],
        # Per-path real action (created/updated/restored/unchanged) —
        # incremental-install evidence the receipt folds into
        # managed_files (cycle 16.1 §7.4).
        "actions": {},
    }

    if write_markers and (
        enabled_kinds is None or "marker" in enabled_kinds
    ):
        # AGENTS.md — the generic contract (Codex, Devin and any agent CLI
        # read it).
        agents_md = root / "AGENTS.md"
        agents_before = agents_md.read_bytes() if agents_md.is_file() else None
        apply_marker_block(agents_md, _BLOCK_BODY)
        ledger = record_file(
            ledger,
            agents_md,
            kind="host_contract",
            mode="markers",
            owned_key_hashes={
                "block": marker_block_sha(agents_md.read_text(encoding="utf-8"))
            },
            host="generic",
        )
        report["marker_files"].append("AGENTS.md")
        after = agents_md.read_bytes()
        report["actions"][agents_md.as_posix()] = (
            "unchanged" if after == agents_before
            else "created" if agents_before is None else "updated"
        )

        # CLAUDE.md — only when it already exists or claude was detected; we
        # don't create host files for hosts that were never seen (§76).
        claude_md = root / "CLAUDE.md"
        if claude_md.is_file() or "claude" in hosts:
            claude_before = (
                claude_md.read_bytes() if claude_md.is_file() else None
            )
            apply_marker_block(claude_md, _BLOCK_BODY)
            ledger = record_file(
                ledger,
                claude_md,
                kind="host_contract",
                mode="markers",
                owned_key_hashes={
                    "block": marker_block_sha(claude_md.read_text(encoding="utf-8"))
                },
                host="claude",
            )
            report["marker_files"].append("CLAUDE.md")
            after = claude_md.read_bytes()
            report["actions"][claude_md.as_posix()] = (
                "unchanged" if after == claude_before
                else "created" if claude_before is None else "updated"
            )
        else:
            report["skipped"].append("CLAUDE.md (host not detected)")

    if with_mirrors and (
        enabled_kinds is None or "agent" in enabled_kinds
    ):
        from sparkforge_azure.skills.mirrors import namespace_knowledge_refs

        sources = _agent_sources()
        if not sources:
            report["skipped"].append("mirrors (no packaged agents found)")
        for agent_id, source_text in sources:
            # install-2.1: `knowledge/<rel>` do espelho resolve contra a
            # raiz compartilhada do alvo — reescrito para o subdir proprio
            # `knowledge/sparkforge-azure/` onde os ponteiros vivem.
            rendered = namespace_knowledge_refs(
                render_agent_mirror(source_text, agent_id))
            for mroot in agent_roots:
                target = root / mroot / f"{mirror_name(agent_id)}.md"
                payload = rendered.encode("utf-8")
                report["mirrors"]["bytes"] += len(payload)
                # install-2.1: arquivo pre-existente nao-ledgered e
                # estrangeiro — preservado, nunca adotado nem sobrescrito.
                ledger, outcome = write_managed_file(
                    ledger,
                    target,
                    rendered,
                    kind="agent_mirror",
                    host=mroot.split("/")[0].lstrip("."),
                )
                if outcome == "preserved_foreign":
                    report["preserved_foreign"].append(str(target))
                    report["skipped"].append(
                        f"{target.name} (foreign file preserved)")
                    report["actions"][target.as_posix()] = "unchanged"
                elif outcome == "unchanged":
                    report["mirrors"]["unchanged"] += 1
                    report["actions"][target.as_posix()] = "unchanged"
                else:
                    # created | updated | restored — real byte writes.
                    report["mirrors"]["written"] += 1
                    report["mirrors"]["written_bytes"] += len(payload)
                    report["actions"][target.as_posix()] = outcome

    return ledger, report


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
