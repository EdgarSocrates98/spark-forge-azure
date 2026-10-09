"""Generated agents catalogue (SDD AGENTS_REFERENCE_DOC)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_agents_doc_in_sync() -> None:
    script = _load_script("gen_agents_doc")
    doc = ROOT / "docs" / "reference" / "agents.md"
    assert doc.is_file(), "gere com: python scripts/gen_agents_doc.py"
    rendered = script.render(ROOT)
    assert doc.read_text(encoding="utf-8") == rendered, (
        "doc stale — rode python scripts/gen_agents_doc.py"
    )
    for agent_id in ALL_AGENT_IDS:
        assert f"`{agent_id}`" in rendered


def test_agents_doc_indexed() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "docs/reference/agents.md" in index
