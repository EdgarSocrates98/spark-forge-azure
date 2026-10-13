"""Output schemas por role (§96-104).

Todo output estruturado de agente valida contra um schema fechado.
Violacao => ``contract_violation`` nomeado (§103) — nunca coercao
silenciosa (§104). Output freeform do host vira PROVISIONAL_AGENT_OUTPUT
(§31); nada vira verified sem verificacao deterministica (§32).
"""

from __future__ import annotations

from typing import Any

from sparkforge_azure.agentmanifest.model import ROLE_IDS, SPECIALIST_IDS

# §30 — formato geral de AgentResult; roles especificas refinam.
_GENERAL_RESULT = (
    "hypotheses",
    "proposed_findings",
    "evidence_refs",
    "unresolved",
    "objections",
    "recommendations",
)

#: schema por "kind" — campos required no structured_output.
ROLE_SCHEMAS: dict[str, tuple[str, ...]] = {
    "extraction_result": ("facts", "unresolved"),
    "inventory_result": ("status_counts",),
    "verdict_result": ("verdicts", "unresolved"),
    # §97 specialist
    "specialist_result": (
        "hypotheses",
        "evidence_refs",
        "proposed_findings",
        "unresolved",
        "recommendations",
    ),
    # §98 reviewer (+ critic/reviewers de dominio)
    "reviewer_result": (
        "accepted",
        "rejected",
        "objections",
        "missing_evidence",
        "risk",
    ),
    # §99 verifier
    "verifier_result": (
        "supported",
        "refuted",
        "insufficient",
        "conflicts",
    ),
    # §100 referee
    "referee_result": (
        "decision",
        "evidence",
        "rejected_positions",
        "unresolved",
    ),
    # §101 test engineer
    "test_engineer_result": (
        "coverage_gaps",
        "proposed_tests",
        "risk_areas",
        "already_covered",
    ),
    # §102 evaluation specialist
    "evaluation_result": (
        "configuration_comparison",
        "quality_delta",
        "cost_delta",
        "agent_value",
        "recommendation",
    ),
    # coordinator / synthesizer / demais roles deterministicas
    "agent_result": _GENERAL_RESULT,
    # §31 — host freeform parseado, nunca verified
    "provisional_agent_output": ("raw", "unresolved"),
}

_REVIEWERS = {
    "reviewer",
    "security-reviewer",
    "cost-reviewer",
    "performance-reviewer",
    "migration-reviewer",
    "critic",
}

_SCHEMA_BY_AGENT: dict[str, str] = {
    "extractor": "extraction_result",
    "inventory": "inventory_result",
    "judge": "verdict_result",
    "verifier": "verifier_result",
    "referee": "referee_result",
    "test-engineer": "test_engineer_result",
    "evaluation-specialist": "evaluation_result",
    **{r: "reviewer_result" for r in _REVIEWERS},
    **{s: "specialist_result" for s in SPECIALIST_IDS},
}


def schema_kind_for(agent_id: str) -> str:
    """Deterministico: agent_id -> kind de schema esperado."""
    if agent_id in _SCHEMA_BY_AGENT:
        return _SCHEMA_BY_AGENT[agent_id]
    if agent_id.endswith("-reviewer"):
        return "reviewer_result"
    if agent_id in ROLE_IDS:
        return "agent_result"
    return "specialist_result" if agent_id in SPECIALIST_IDS else "agent_result"


def validate_output(
    agent_id: str, structured: dict[str, Any] | None
) -> list[str]:
    """Fail-closed: lista de violacoes; [] = conforme o schema do role."""
    expected = schema_kind_for(agent_id)
    if structured is None:
        return ["contract_violation:missing_structured_output"]
    kind = structured.get("kind")
    if kind != expected:
        # freeform parseado e aceito como provisional (§31)
        if kind == "provisional_agent_output":
            missing = [
                f for f in ROLE_SCHEMAS["provisional_agent_output"]
                if f not in structured
            ]
            return [f"contract_violation:missing:{f}" for f in missing]
        return [f"contract_violation:kind:{kind!r}!={expected!r}"]
    missing = [f for f in ROLE_SCHEMAS[kind] if f not in structured]
    return [f"contract_violation:missing:{f}" for f in missing]


def parse_freeform(agent_id: str, text: str) -> dict[str, Any]:
    """§31 — texto do host vira PROVISIONAL_AGENT_OUTPUT, nunca verified."""
    return {
        "kind": "provisional_agent_output",
        "agent_id": agent_id,
        "raw": text,
        "unresolved": ["freeform_output_requires_verification"],
    }
