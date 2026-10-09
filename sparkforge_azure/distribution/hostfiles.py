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
)
from sparkforge_azure.durable import write_atomic

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


def install_host_assets(
    root: Path,
    ledger: dict[str, Any],
    *,
    hosts: tuple[str, ...] = (),
    with_mirrors: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write the host-facing files; returns (ledger, report)."""
    report: dict[str, Any] = {
        "marker_files": [],
        "mirrors": {"written": 0, "roots": list(AGENT_MIRROR_ROOTS)},
        "skipped": [],
    }

    # AGENTS.md — the generic contract (Codex, Devin and any agent CLI read it).
    agents_md = root / "AGENTS.md"
    apply_marker_block(agents_md, _BLOCK_BODY)
    ledger = record_file(
        ledger,
        agents_md,
        kind="host_contract",
        mode="markers",
        owned_key_hashes={"block": marker_block_sha(agents_md.read_text(encoding="utf-8"))},
        host="generic",
    )
    report["marker_files"].append("AGENTS.md")

    # CLAUDE.md — only when it already exists or claude was detected; we
    # don't create host files for hosts that were never seen (§76).
    claude_md = root / "CLAUDE.md"
    if claude_md.is_file() or "claude" in hosts:
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
    else:
        report["skipped"].append("CLAUDE.md (host not detected)")

    if with_mirrors:
        sources = _agent_sources()
        if not sources:
            report["skipped"].append("mirrors (no packaged agents found)")
        for agent_id, source_text in sources:
            rendered = render_agent_mirror(source_text, agent_id)
            for mroot in AGENT_MIRROR_ROOTS:
                target = root / mroot / f"{mirror_name(agent_id)}.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                write_atomic(target, rendered)
                ledger = record_file(
                    ledger,
                    target,
                    kind="agent_mirror",
                    mode="file",
                    host=mroot.split("/")[0].lstrip("."),
                )
                report["mirrors"]["written"] += 1

    return ledger, report


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
