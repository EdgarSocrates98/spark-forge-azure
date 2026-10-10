"""Runtime surface — SDD AGENT_RUNTIME_SURFACE (§122, §146-151, §173)."""
from __future__ import annotations

import argparse

from sparkforge_azure.agentic.execution import run_case
from sparkforge_azure.agentic.spans import spans_from_execution
from sparkforge_azure.cli import cmd_agents
from sparkforge_azure.mcp.tools import TOOLS


def _args(**kw) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def test_spans_carry_runtime_fields() -> None:
    receipt = run_case({
        "id": "s1", "task": "unity catalog denied",
        "unresolved": ["unity-catalog:grant"],
        "context": {"evidence": [{"ref": "x"}]},
    })
    spans = spans_from_execution(receipt)
    assert spans, "receipt deveria produzir spans"
    for span in spans:
        assert span.runtime == "generic"
        assert span.execution_mode in {"inline", "playbook"}
        assert span.runtime_spawn_id.startswith("sp-")
        assert span.output_valid is not None
    d = spans[0].to_dict()
    for f in ("runtime", "execution_mode", "runtime_spawn_id",
              "output_valid", "tool_calls"):
        assert f in d


def test_cli_dry_run() -> None:
    out = cmd_agents._execute(_args(
        task="streaming lag event hubs", runtime="generic", max_agents=3))
    assert out["dry_run"] is True
    assert out["planned_stages"]
    assert out["route"]
    assert out["stage_fingerprints"]
    assert all(v.startswith("sha256:") for v in
               out["stage_fingerprints"].values())
    assert out["execution_mode"] == "inline"


def test_agents_verbs_resolve_fleet_outside_repo(tmp_path, monkeypatch) -> None:
    """Regressão: num projeto instalado o cwd não tem `agents/` — os verbos
    `agents` leem a frota via `fleet_root()` (repo ou `_data` empacotado),
    nunca o diretório do usuário."""
    monkeypatch.chdir(tmp_path)
    listed = cmd_agents._list(_args())
    assert listed["counts"].get("broken", 0) == 0
    assert len(listed["agents"]) > 0
    fp = cmd_agents._fingerprint(_args())
    assert fp["status"] == "ok"
    out = cmd_agents._execute(_args(
        task="adf copy activity lenta", runtime="generic", max_agents=3))
    assert out["stage_fingerprints"]
    assert all(v.startswith("sha256:") for v in
               out["stage_fingerprints"].values())


def test_mcp_tools_readonly() -> None:
    assert "sfa_agents_runtimes" in TOOLS
    assert "sfa_agents_execution_explain" in TOOLS
    for name in ("sfa_agents_runtimes", "sfa_agents_execution_explain"):
        assert TOOLS[name].risk.read_only is True
        assert TOOLS[name].risk.cloud_write is False
    rt = TOOLS["sfa_agents_runtimes"].handler({})
    assert "runtimes" in rt and len(rt["runtimes"]) == 6
    ex = TOOLS["sfa_agents_execution_explain"].handler(
        {"prompt": "fabric lakehouse shortcut denied"})
    assert ex["planned_stages"]
    assert ex["execution_mode"] in {"inline", "playbook", "subagent"}


def test_doctor_agent_runtime() -> None:
    from sparkforge_azure.doctor import run

    out = run(["agent_runtime"])
    check = out["checks"][0]
    assert check["area"] == "agent_runtime"
    assert check["status"] == "ok"
    assert len(check["detail"]) > 0
