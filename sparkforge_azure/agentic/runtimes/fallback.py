"""Fallback / degradacao explicita (§77-86, §200-206).

Ordem §77: real agent -> sequential -> playbook -> deterministic core.
Toda degradacao devolve ``degraded_reason`` nomeado — degradacao
silenciosa e defeito (§79). Retry so em falha transiente, uma vez, com
fingerprint (§83-84, §206): nunca loop de retry caro.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sparkforge_azure.agentic.runtime import RuntimeName

from .base import (
    AgentSpawnRequestV2,
    AgentSpawnResultV2,
)
from .registry import get_adapter

#: §83/§204-205 — so estes failure_kinds justificam UMA retentativa.
TRANSIENT_FAILURES = {"timeout", "rate_limit"}

#: ordem de fallback §77 a partir de um runtime preferido.
_FLOORS = (RuntimeName.CODEX, RuntimeName.GENERIC)  # playbook -> inline


def fallback_chain(preferred: RuntimeName) -> list[RuntimeName]:
    """§77 — preferred, depois floors ate o deterministico."""
    chain = [preferred]
    for floor in _FLOORS:
        if floor not in chain:
            chain.append(floor)
    return chain


@dataclass
class FallbackResult:
    """Resultado + trilha de degradacao (§78)."""

    result: AgentSpawnResultV2
    runtime_used: str
    degraded: bool
    degraded_reason: str | None = None
    attempts: list[dict[str, str]] = field(default_factory=list)


def execute_with_fallback(
    request: AgentSpawnRequestV2,
    preferred: RuntimeName,
) -> FallbackResult:
    """Tenta o runtime preferido; degrada pela cadeia §77 com razao."""
    attempts: list[dict[str, str]] = []
    for runtime in fallback_chain(preferred):
        adapter = get_adapter(runtime)
        result = adapter.spawn_agent(request)
        attempts.append({
            "runtime": runtime.value,
            "status": result.status,
            "failure": result.failure_kind() or "",
        })
        if result.status in {"completed", "unresolved"}:
            degraded = runtime != preferred
            return FallbackResult(
                result=result,
                runtime_used=runtime.value,
                degraded=degraded,
                degraded_reason=(
                    f"{preferred.value}_unavailable->{runtime.value}"
                    if degraded else None
                ),
                attempts=attempts,
            )
        kind = result.failure_kind() or "spawn_failed"
        # §83-84 — transiente retenta UMA vez no mesmo runtime
        if kind in TRANSIENT_FAILURES:
            retry = adapter.spawn_agent(request)
            attempts.append({
                "runtime": runtime.value,
                "status": retry.status,
                "failure": f"retry:{retry.failure_kind() or ''}",
            })
            if retry.status in {"completed", "unresolved"}:
                degraded = runtime != preferred
                return FallbackResult(
                    result=retry,
                    runtime_used=runtime.value,
                    degraded=degraded,
                    degraded_reason=(
                        f"{preferred.value}_unavailable->{runtime.value}"
                        if degraded else None
                    ),
                    attempts=attempts,
                )
        # permanente -> proximo degrau da cadeia
    last = attempts[-1]
    return FallbackResult(
        result=result,
        runtime_used=last["runtime"],
        degraded=True,
        degraded_reason=f"all_fallbacks_exhausted:{last['failure']}",
        attempts=attempts,
    )
