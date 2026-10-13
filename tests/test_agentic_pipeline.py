"""Canonical §30 base agent graph + conditional branches (BASE_AGENT_PIPELINE)."""
from __future__ import annotations

from sparkforge_azure.agentic.pipeline import (
    BASE_AGENT_PIPELINE,
    plan_pipeline,
)
from sparkforge_azure.agentmanifest.model import ALL_AGENT_IDS


def test_base_pipeline_order() -> None:
    ids = [s.slot for s in BASE_AGENT_PIPELINE]
    assert ids == [
        "coordinator", "inventory", "extractor", "analyzer", "specialist",
        "judge", "verifier", "reviewer", "critic", "referee", "synthesizer",
    ]
    required = [s.slot for s in BASE_AGENT_PIPELINE if s.required]
    assert required == [
        "coordinator", "inventory", "extractor", "analyzer",
        "judge", "verifier", "synthesizer",
    ]


def test_conditional_branches() -> None:
    chain = plan_pipeline(
        specialist_id="unity-catalog-specialist",
        needs_review=True,
        has_conflict=True,
        needs_referee=True,
    )
    assert chain == [
        "coordinator", "inventory", "extractor", "analyzer",
        "unity-catalog-specialist", "judge", "verifier",
        "reviewer", "critic", "referee", "synthesizer",
    ]
    sparse = plan_pipeline()
    assert sparse == [
        "coordinator", "inventory", "extractor", "analyzer",
        "judge", "verifier", "synthesizer",
    ]


def test_fast_path_skips_optionals() -> None:
    # §32: complete evidence + low risk -> Verifier -> Synthesizer
    chain = plan_pipeline(
        specialist_id="adls-specialist",
        needs_review=True,
        has_conflict=True,
        needs_referee=True,
        evidence_complete=True,
        low_risk=True,
    )
    assert "adls-specialist" not in chain
    assert not {"reviewer", "critic", "referee"} & set(chain)
    assert chain[-2:] == ["verifier", "synthesizer"]


def test_stages_resolve_to_real_agents() -> None:
    for stage in BASE_AGENT_PIPELINE:
        if stage.slot == "specialist":
            continue  # slot filled by the routed specialist id
        assert stage.agent_id in ALL_AGENT_IDS
    chain = plan_pipeline(specialist_id="streaming-specialist")
    assert set(chain) <= set(ALL_AGENT_IDS)
