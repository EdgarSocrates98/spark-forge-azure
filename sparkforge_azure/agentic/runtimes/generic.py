"""Adapters INLINE / PLAYBOOK — o floor real (§15-16).

Um adapter playbook NAO finge multi-agent: roda a role como funcao
deterministica do core quando ela existe em ``INLINE_EXECUTORS`` —
extractor/inventory/judge sao L0 e ja sao quase inteiramente
deterministicas (§225). Role sem executor deterministico devolve
``unresolved`` com razao nomeada — nunca "would spawn" (§14, §16).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from sparkforge_azure.agentic.runtime import RuntimeName

from .base import (
    AgentSpawnRequestV2,
    AgentSpawnResultV2,
    BaseAdapter,
    new_spawn_id,
)


def _exec_extractor(request: AgentSpawnRequestV2) -> dict[str, Any]:
    """Facts sao PROVISIONAL — agent nao cria verified fact (§32)."""
    evidence = request.context.get("evidence") or []
    facts = [
        {
            "id": f"fact-{i}",
            "ref": str(item.get("ref", item)),
            "kind": "provisional",
        }
        for i, item in enumerate(evidence)
    ]
    return {
        "kind": "extraction_result",
        "facts": facts,
        "unresolved": [] if evidence else ["no_evidence_items"],
    }


def _exec_inventory(request: AgentSpawnRequestV2) -> dict[str, Any]:
    from sparkforge_azure.agentic.inventory import inventory

    root = request.context.get("root", ".")
    inv = inventory(Path(root))
    return {
        "kind": "inventory_result",
        "status_counts": dict(inv.counts),
    }


def _exec_judge(request: AgentSpawnRequestV2) -> dict[str, Any]:
    claims = request.context.get("claims") or []
    if not claims:
        return {
            "kind": "verdict_result",
            "unresolved": ["no_claims_provided"],
            "verdicts": [],
        }
    verdicts = [
        {
            "claim": str(c.get("claim", c)),
            "verdict": "INSUFFICIENT",
            "reason": "inline judge requires evidence verification pass",
        }
        for c in claims
    ]
    return {"kind": "verdict_result", "verdicts": verdicts, "unresolved": []}


def _exec_verifier(request: AgentSpawnRequestV2) -> dict[str, Any]:
    """§34 — falsificacao deterministica: finding sem evidence_ref cai.

    Verifier inline nao prova nada probabilistico — aplica a unica regra
    deterministicamente verificavel: todo proposed finding precisa de
    evidencia citada. Resultado usa o vocab §99.
    """
    findings = request.context.get("proposed_findings") or []
    supported, refuted, insufficient = [], [], []
    for f in findings:
        has_ev = isinstance(f, dict) and f.get("evidence_refs")
        (supported if has_ev else refuted).append(str(f))
    for u in request.context.get("prior_unresolved") or []:
        insufficient.append(str(u))
    return {
        "kind": "verifier_result",
        "supported": supported,
        "refuted": refuted,
        "insufficient": insufficient,
        "conflicts": list(request.context.get("conflicts") or []),
    }


def _exec_synthesizer(request: AgentSpawnRequestV2) -> dict[str, Any]:
    """§221-223 — sintese deterministica: render estruturado do estado.

    Candidato a "economy win": casos simples nao precisam de LLM para
    compor o relatorio — findings verificados + unresolved preservados.
    """
    return {
        "kind": "agent_result",
        "hypotheses": [],
        "proposed_findings": list(
            request.context.get("proposed_findings") or []
        ),
        "evidence_refs": [],
        "unresolved": list(request.context.get("prior_unresolved") or []),
        "objections": [],
        "recommendations": list(
            request.context.get("recommendations") or []
        ),
    }


#: Roles que executam de verdade sem host — deterministicas (§225-226).
INLINE_EXECUTORS = {
    "extractor": _exec_extractor,
    "inventory": _exec_inventory,
    "judge": _exec_judge,
    "verifier": _exec_verifier,
    "synthesizer": _exec_synthesizer,
}


class InlineAdapter(BaseAdapter):
    """Runtime generico: executa o que e deterministico, recusa o resto."""

    name = RuntimeName.GENERIC
    status = "adapter_implemented"
    execution_mode = "inline"

    def spawn_agent(self, request: AgentSpawnRequestV2) -> AgentSpawnResultV2:
        started = time.time()
        executor = INLINE_EXECUTORS.get(request.agent_id)
        if executor is None:
            return AgentSpawnResultV2(
                agent_id=request.agent_id,
                spawn_id=new_spawn_id(request.agent_id),
                runtime=self.name.value,
                execution_mode=self.execution_mode,
                status="unresolved",
                started=started,
                completed=time.time(),
                structured_output={
                    "unresolved": "requires_probabilistic_reasoning",
                    "fallback": "spawn via host adapter when proven",
                },
            )
        return AgentSpawnResultV2(
            agent_id=request.agent_id,
            spawn_id=new_spawn_id(request.agent_id),
            runtime=self.name.value,
            execution_mode=self.execution_mode,
            status="completed",
            started=started,
            completed=time.time(),
            structured_output=executor(request),
        )


class GenericAdapter(InlineAdapter):
    """Alias semantico: generic = INLINE floor."""
