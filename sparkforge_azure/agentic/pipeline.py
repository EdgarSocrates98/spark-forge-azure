"""Canonical base agent chain (§30) with conditional branches (§31–32).

``BASE_AGENT_PIPELINE`` declares the eleven stages in §30 order — seven
required, four conditional. ``plan_pipeline`` prunes the conditional stages
deterministically: the §32 fast path (complete evidence + low risk) skips
specialist/reviewer/critic/referee and goes straight Verifier → Synthesizer.

This is a *plan*, not an executor — it names which agents would run so the
coordinator, the spawn gate and tests all share one chain definition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineStage:
    """One stage of the §30 chain.

    ``slot`` is the position name; ``agent_id`` is the concrete role —
    ``None`` for the ``specialist`` slot, filled by the routed id.
    """

    slot: str
    agent_id: str | None
    required: bool


BASE_AGENT_PIPELINE: tuple[PipelineStage, ...] = (
    PipelineStage("coordinator", "coordinator", True),
    PipelineStage("inventory", "inventory", True),
    PipelineStage("extractor", "extractor", True),
    PipelineStage("analyzer", "analyzer", True),
    PipelineStage("specialist", None, False),
    PipelineStage("judge", "judge", True),
    PipelineStage("verifier", "verifier", True),
    PipelineStage("reviewer", "reviewer", False),
    PipelineStage("critic", "critic", False),
    PipelineStage("referee", "referee", False),
    PipelineStage("synthesizer", "synthesizer", True),
)


def plan_pipeline(
    *,
    specialist_id: str | None = None,
    needs_review: bool = False,
    has_conflict: bool = False,
    needs_referee: bool = False,
    evidence_complete: bool = False,
    low_risk: bool = False,
) -> list[str]:
    """Concrete agent id sequence for one case, deterministic.

    Fast path (§32): ``evidence_complete and low_risk`` prunes every
    conditional stage. Otherwise each conditional is kept when its trigger
    holds: specialist slot filled by the routed ``specialist_id``, reviewer
    on ``needs_review``, critic on ``has_conflict``, referee on
    ``needs_referee``.
    """
    fast_path = evidence_complete and low_risk
    on = {
        "specialist": specialist_id if specialist_id and not fast_path else None,
        "reviewer": needs_review and not fast_path,
        "critic": has_conflict and not fast_path,
        "referee": needs_referee and not fast_path,
    }
    chain: list[str] = []
    for stage in BASE_AGENT_PIPELINE:
        if stage.required:
            chain.append(stage.slot)
            continue
        active = on[stage.slot]
        if active:
            chain.append(active if isinstance(active, str) else stage.slot)
    return chain
