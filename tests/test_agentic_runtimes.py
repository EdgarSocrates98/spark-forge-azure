"""Runtime adapters — SDD AGENT_RUNTIME_ADAPTERS (§11-22)."""
from __future__ import annotations

from pathlib import Path

import pytest

from sparkforge_azure.agentic.runtime import RuntimeName
from sparkforge_azure.agentic.runtimes import (
    EXECUTION_MODES,
    RUNTIME_STATUSES,
    USAGE_STATUSES,
    AgentSpawnRequestV2,
    get_adapter,
    runtime_registry,
)


def test_closed_vocabularies() -> None:
    assert EXECUTION_MODES == {
        "inline", "playbook", "sequential_agent",
        "parallel_agent", "subagent",
    }
    assert USAGE_STATUSES == {"measured", "unresolved", "not_available"}
    assert RUNTIME_STATUSES == {
        "declared", "adapter_implemented", "integration_tested",
        "host_proven", "evaluated", "degraded", "unavailable",
    }


def test_spawn_result_v2_fields() -> None:
    adapter = get_adapter(RuntimeName.GENERIC)
    result = adapter.spawn_agent(AgentSpawnRequestV2(
        agent_id="extractor",
        task="extract facts",
    ))
    for field in (
        "agent_id", "spawn_id", "runtime", "execution_mode", "status",
        "output", "structured_output", "error", "usage", "trace_ref",
    ):
        assert hasattr(result, field), f"missing {field}"
    assert result.execution_mode in EXECUTION_MODES
    assert result.usage["status"] in USAGE_STATUSES


def test_registry_status_honesty() -> None:
    registry = runtime_registry()
    assert set(registry) == set(RuntimeName)
    for name, entry in registry.items():
        assert entry["status"] in RUNTIME_STATUSES
        if entry["status"] == "host_proven":
            assert entry["proof"], (
                f"{name}: host_proven exige prova (§9)"
            )
    # host_proven so com transcript gravado em evals/host_proof/
    host_runtimes = {
        RuntimeName.CLAUDE_CODE, RuntimeName.DEVIN_CLI,
        RuntimeName.DEVIN_DESKTOP, RuntimeName.CODEX,
    }
    for name in host_runtimes:
        st = registry[name]["status"]
        if st == "host_proven":
            proof = registry[name]["proof"]
            assert proof and Path(proof).is_file(), (
                f"{name}: host_proven sem artefato de prova"
            )
        else:
            assert st in {"declared", "adapter_implemented", "unavailable"}


def test_playbook_executes_deterministic_role() -> None:
    adapter = get_adapter(RuntimeName.GENERIC)
    result = adapter.spawn_agent(AgentSpawnRequestV2(
        agent_id="extractor",
        task="extract",
    ))
    assert result.execution_mode == "inline"
    assert result.status == "completed"
    assert result.error is None


def test_host_adapter_fail_closed() -> None:
    for name in (RuntimeName.CLAUDE_CODE, RuntimeName.DEVIN_CLI,
                 RuntimeName.DEVIN_DESKTOP, RuntimeName.CODEX):
        adapter = get_adapter(name)
        result = adapter.spawn_agent(AgentSpawnRequestV2(
            agent_id="unity-catalog-specialist",
            task="diagnose",
        ))
        if result.status == "failed":
            assert result.error is not None
            assert "unavailable" in result.error or "unproven" in result.error


def test_no_fake_adapter_language() -> None:
    adapter = get_adapter(RuntimeName.CODEX)
    result = adapter.spawn_agent(AgentSpawnRequestV2(
        agent_id="fabric-specialist", task="x"))
    assert "would spawn" not in (result.output or "")


@pytest.mark.parametrize("name", list(RuntimeName))
def test_every_runtime_resolves_adapter(name: RuntimeName) -> None:
    assert get_adapter(name) is not None
