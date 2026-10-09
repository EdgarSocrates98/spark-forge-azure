"""Freeze gate — SDD AGENTIC_ARCHITECTURE_FREEZE (§179-191)."""
from __future__ import annotations

from pathlib import Path

from sparkforge_azure.agentic.freeze import FREEZE_CONDITIONS, evaluate_freeze

DOCS = [
    "docs/agentic/RUNTIME_EXECUTION_AUDIT.md",
    "docs/agentic/RUNTIME_ADAPTERS.md",
    "docs/agentic/HOST_EXECUTION.md",
    "docs/agentic/EMPIRICAL_AGENT_VALUE.md",
    "docs/agentic/AGENTIC_ARCHITECTURE_FREEZE.md",
    "docs/agentic/RUNTIME_EXECUTION_OUTCOME.md",
]

OUTCOME_FIELDS = (
    "BASE_SHA", "FINAL_SHA", "RUNTIMES_DECLARED", "RUNTIMES_ADAPTER_IMPLEMENTED",
    "RUNTIMES_HOST_PROVEN", "AGENTS_CONTRACT_READY", "AGENTS_HOST_EXECUTED",
    "AGENTS_VALUE_PROVEN", "QUALITY_FRONTIER", "SECURITY", "BUDGET", "CONTEXT",
    "AGENTOPS", "CLAIMS", "SURFACE", "TESTS", "FREEZE_STATUS",
)


def test_freeze_conditions_evidence() -> None:
    out = evaluate_freeze()
    names = {c["name"] for c in out["conditions"]}
    assert names == set(FREEZE_CONDITIONS)
    # nada 'met' sem evidencia nomeada; host provado via transcript gravado
    by_name = {c["name"]: c for c in out["conditions"]}
    host = by_name["host_execution_proven"]
    assert host["status"] in {"met", "unmet"}
    if host["status"] == "met":
        assert Path("evals/host_proof/claude_code.json").is_file()
    else:
        assert host["blocker"] == "host_proof_missing"
    # sem value eval empirica em host, freeze nao fecha
    if by_name["critical_specialists_evaluated"]["status"] != "met":
        assert out["freeze_status"] == "candidate"


def test_outcome_brief_fields() -> None:
    text = Path("docs/agentic/RUNTIME_EXECUTION_OUTCOME.md").read_text(
        encoding="utf-8")
    for field in OUTCOME_FIELDS:
        assert field in text, f"outcome sem {field}"


def test_required_docs_exist() -> None:
    for doc in DOCS:
        assert Path(doc).is_file(), f"faltando {doc}"
