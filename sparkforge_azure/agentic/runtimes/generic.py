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


#: Roles que executam de verdade sem host — deterministicas (§225-226).
INLINE_EXECUTORS = {
    "extractor": _exec_extractor,
    "inventory": _exec_inventory,
    "judge": _exec_judge,
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
