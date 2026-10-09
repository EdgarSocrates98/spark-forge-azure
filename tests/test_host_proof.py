"""Host proof recorded — SDD HOST_PROOF_RECORDED (§9, §88)."""
from __future__ import annotations

import json
from pathlib import Path

from sparkforge_azure.agentic.runtime import RuntimeName
from sparkforge_azure.agentic.runtimes import get_adapter, runtime_registry
from sparkforge_azure.agentic.runtimes.host import HostCLIAdapter

PROOF = Path("evals/host_proof/claude_code.json")


def test_proof_artifact_schema() -> None:
    assert PROOF.is_file(), "transcript de prova ausente"
    rec = json.loads(PROOF.read_text(encoding="utf-8"))
    assert rec["status"] == "completed"
    assert rec["runtime"] == "claude_code"
    assert str(rec["trace_ref"]).startswith("sha256:")
    assert rec["proof_kind"] == "minimal_ping"
    # custo/tokens medidos de verdade — nunca unresolved numa prova real
    assert rec["usage"]["status"] == "measured"


def test_status_derives_from_artifact(tmp_path) -> None:
    adapter = get_adapter(RuntimeName.CLAUDE_CODE)
    assert adapter.status == "host_proven"
    assert adapter.proof and "claude_code.json" in adapter.proof
    # hosts sem transcript proprio NAO promovem
    for name in (RuntimeName.DEVIN_CLI, RuntimeName.DEVIN_DESKTOP,
                 RuntimeName.CODEX):
        assert get_adapter(name).status == "adapter_implemented"


def test_corrupt_proof_never_promotes(tmp_path, monkeypatch) -> None:
    class FakeHost(HostCLIAdapter):
        name = RuntimeName.DEVIN_CLI
        binary = "x"

    fake = FakeHost()
    monkeypatch.setattr(fake, "_proof_dir", lambda: tmp_path)
    # sem artefato
    assert fake.status == "adapter_implemented"
    # artefato invalido (status != completed)
    (tmp_path / "devin_cli.json").write_text(
        json.dumps({"status": "failed"}), encoding="utf-8")
    assert fake.status == "adapter_implemented"
    # artefato sem trace_ref
    (tmp_path / "devin_cli.json").write_text(
        json.dumps({"status": "completed"}), encoding="utf-8")
    assert fake.status == "adapter_implemented"
    # artefato valido promove
    (tmp_path / "devin_cli.json").write_text(
        json.dumps({"status": "completed", "trace_ref": "sha256:abc"}),
        encoding="utf-8")
    assert fake.status == "host_proven"


def test_registry_reports_proof() -> None:
    reg = runtime_registry()
    entry = reg[RuntimeName.CLAUDE_CODE]
    assert entry["status"] == "host_proven"
    assert entry["proof"] and "evals/host_proof" in entry["proof"]
    # freeze passa a ver host_execution_proven=met
    from sparkforge_azure.agentic.freeze import evaluate_freeze

    out = evaluate_freeze()
    by_name = {c["name"]: c for c in out["conditions"]}
    assert by_name["host_execution_proven"]["status"] == "met"
    assert "host_proof_missing" not in out["blockers"]
