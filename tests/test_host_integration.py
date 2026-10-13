"""W5 — host integration (prompt_evo_portable.md §65–§79).

`distribution init` writes managed host-facing files: the `.mcp.json` MCP
key (W1), a delimited marker block in `AGENTS.md`/`CLAUDE.md`, and — only
with `--with-mirrors` — the agent catalog rendered into the conventional
`.claude/agents/custom/` + `.agents/agents/` roots by the same generator
the repo uses. Everything is ledger-recorded, so `detach` strips our block
and removes our mirrors while preserving user content byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path

from sparkforge_azure.distribution import service
from sparkforge_azure.distribution.detach import detach
from sparkforge_azure.distribution.managed import (
    MARKER_BEGIN,
    assess_ledger,
    load_ledger,
    marker_block_sha,
)


def test_init_writes_managed_marker_block(tmp_path: Path) -> None:
    out = service.initialize(tmp_path)
    agents_md = tmp_path / "AGENTS.md"
    assert agents_md.is_file()
    assert MARKER_BEGIN in agents_md.read_text(encoding="utf-8")
    assert "AGENTS.md" in out["host_files"]["marker_files"]
    # ledger records it as markers mode
    kinds = {
        (f["kind"], f["mode"])
        for f in load_ledger(tmp_path / ".sparkforge-azure")["files"]
    }
    assert ("host_contract", "markers") in kinds


def test_marker_block_coexists_with_user_content(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text(
        "# Team rules\nDo not deploy on Fridays.\n", encoding="utf-8"
    )
    service.initialize(tmp_path)
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Do not deploy on Fridays." in text
    assert MARKER_BEGIN in text
    # re-init updates only inside the markers
    service.initialize(tmp_path)
    again = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert again == text
    assert "Do not deploy on Fridays." in again


def test_claude_md_only_when_host_seen(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        service, "detect_hosts", lambda: tuple()
    )
    service.initialize(tmp_path)
    assert not (tmp_path / "CLAUDE.md").exists()  # host absent → no file
    (tmp_path / "CLAUDE.md").write_text("# existing\n", encoding="utf-8")
    service.initialize(tmp_path)  # file exists → managed block lands
    assert MARKER_BEGIN in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


def test_mirrors_opt_in_and_ledgered(tmp_path: Path) -> None:
    out = service.initialize(tmp_path)
    assert out["host_files"]["mirrors"]["written"] == 0
    assert not (tmp_path / ".claude").exists()

    out = service.initialize(tmp_path, with_mirrors=True)
    written = out["host_files"]["mirrors"]["written"]
    assert written > 0
    assert written % 2 == 0  # two mirror roots per agent
    claude = tmp_path / ".claude" / "agents" / "custom"
    generic = tmp_path / ".agents" / "agents"
    assert claude.is_dir() and generic.is_dir()
    sample = next(claude.glob("sparkforge-azure-*.md"))
    assert "GENERATED" in sample.read_text(encoding="utf-8")
    assert (generic / sample.name).is_file()  # same render, second root


def test_detach_strips_block_preserves_user_text(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# mine\n", encoding="utf-8")
    service.initialize(tmp_path, with_mirrors=True)
    out = detach(tmp_path)
    actions = {d["action"] for d in out["detached"]}
    assert "stripped_block" in actions
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert MARKER_BEGIN not in text
    assert "# mine" in text
    # mirrors removed, state kept by default
    assert not list((tmp_path / ".claude").rglob("*.md"))
    assert (tmp_path / ".sparkforge-azure" / "project.yaml").is_file()


def test_detach_modified_managed_file_preserved(tmp_path: Path) -> None:
    service.initialize(tmp_path, with_mirrors=True)
    mirror = next((tmp_path / ".claude").rglob("sparkforge-azure-*.md"))
    mirror.write_text("user rewrote this\n", encoding="utf-8")
    out = detach(tmp_path)
    modified = [d for d in out["detached"] if d["action"] == "preserved_modified"]
    assert any(d["path"].endswith(mirror.name) for d in modified)
    assert mirror.read_text(encoding="utf-8") == "user rewrote this\n"


def test_marker_drift_reported_not_silent(tmp_path: Path) -> None:
    service.initialize(tmp_path)
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text("user deleted the whole block\n", encoding="utf-8")
    drift = assess_ledger(tmp_path / ".sparkforge-azure")
    entry = next(d for d in drift if d["path"].endswith("AGENTS.md"))
    assert entry["state"] == "modified"


def test_marker_sha_changes_with_block(tmp_path: Path) -> None:
    service.initialize(tmp_path)
    sha = marker_block_sha((tmp_path / "AGENTS.md").read_text(encoding="utf-8"))
    assert sha and len(sha) == 64
    assert marker_block_sha("no markers here") is None
