"""Host mirrors of the agent manifests (SDD AGENT_MIRRORS).

``agents/<id>.md`` is the single source. Mirrors are generated into
``.claude/agents/custom/`` and ``.agents/agents/`` with a ``sparkforge-azure-``
prefixed ``name`` and ``description`` taken from ``mission``.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from sparkforge_azure.agentmanifest import mirrors
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS

REPO = Path(__file__).resolve().parents[1]


def _tree(tmp_path: Path) -> Path:
    shutil.copytree(REPO / "agents", tmp_path / "agents")
    return tmp_path


def test_render_agent_mirror() -> None:
    src = (REPO / "agents" / "coordinator.md").read_text(encoding="utf-8")
    out = mirrors.render_agent_mirror(src, "coordinator")
    assert out == mirrors.render_agent_mirror(src.replace("\n", "\r\n"), "coordinator")
    assert "name: sparkforge-azure-coordinator" in out
    assert "description:" in out
    assert "<!-- GENERATED from agents/coordinator.md; do not edit -->" in out
    assert "schema_version: 2" in out


def test_agent_mirror_drift_and_sync(tmp_path) -> None:
    root = _tree(tmp_path)
    drift = {d.reason for d in mirrors.check_agent_mirrors(root)}
    assert drift == {"missing"}

    changed = mirrors.sync_agent_mirrors(root)
    assert changed
    assert mirrors.check_agent_mirrors(root) == []
    assert len(list((root / ".agents" / "agents").glob("*.md"))) == len(ALL_AGENT_IDS)

    target = root / ".agents" / "agents" / "sparkforge-azure-coordinator.md"
    target.write_text("tampered", encoding="utf-8")
    assert {d.reason for d in mirrors.check_agent_mirrors(root)} == {"stale"}

    orphan = root / ".claude" / "agents" / "custom" / "sparkforge-azure-ghost.md"
    orphan.write_text("x", encoding="utf-8")
    assert "orphan" in {d.reason for d in mirrors.check_agent_mirrors(root)}

    mirrors.sync_agent_mirrors(root)
    assert not orphan.exists()
    assert mirrors.check_agent_mirrors(root) == []


def test_real_tree_agent_mirrors_in_sync() -> None:
    assert mirrors.check_agent_mirrors(REPO) == []


def test_check_script_reports_agent_mirrors() -> None:
    out = subprocess.run(
        [sys.executable, "scripts/check_skills_agents.py", "--root", "."],
        capture_output=True, text=True, cwd=REPO,
    )
    report = json.loads(out.stdout)
    assert "agent_mirrors_in_sync" in report
    assert report["agent_mirrors_in_sync"] is True
