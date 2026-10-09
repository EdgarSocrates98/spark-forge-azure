"""Base do adapter boundary (§11-19).

Core → AgentRuntime protocol → HostAdapter. Nenhum SDK de host entra no
core (§12): o adapter recebe o pedido materializado e devolve um
``AgentSpawnResultV2`` cujo ``output`` é sempre DATA_ONLY (§29).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sparkforge_azure.agentic.runtime import RuntimeCapabilities, RuntimeName

# §17 — vocabulario fechado de como o agente de fato executou.
EXECUTION_MODES = {
    "inline",
    "playbook",
    "sequential_agent",
    "parallel_agent",
    "subagent",
}

# §19 — uso de tokens/custo so quando observado de verdade.
USAGE_STATUSES = {"measured", "unresolved", "not_available"}

# §7 — status do runtime: declarar != prover.
RUNTIME_STATUSES = {
    "declared",
    "adapter_implemented",
    "integration_tested",
    "host_proven",
    "evaluated",
    "degraded",
    "unavailable",
}

# §81 — taxonomia fechada de falha de runtime.
FAILURE_KINDS = {
    "runtime_unavailable",
    "spawn_failed",
    "timeout",
    "rate_limit",
    "tool_unavailable",
    "invalid_structured_output",
    "budget_exceeded",
    "host_capability_mismatch",
}


@dataclass(frozen=True)
class AgentSpawnRequestV2:
    """Pedido materializado de spawn — resolveu manifest+plan+gate antes."""

    agent_id: str
    task: str
    context: dict[str, Any] = field(default_factory=dict)
    context_refs: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    budget_tokens: int | None = None
    timeout_seconds: int = 120
    autonomy: str = "L1"
    case_fingerprint: str = ""


@dataclass
class AgentSpawnResultV2:
    """§18 — resultado canonico de um spawn."""

    agent_id: str
    spawn_id: str
    runtime: str
    execution_mode: str
    status: str  # completed | failed | running | unresolved
    started: float = 0.0
    completed: float | None = None
    output: str = ""
    structured_output: dict[str, Any] | None = None
    error: str | None = None
    usage: dict[str, Any] = field(
        default_factory=lambda: {"status": "not_available"}
    )
    trace_ref: str | None = None

    def __post_init__(self) -> None:
        if self.execution_mode not in EXECUTION_MODES:
            raise ValueError(f"execution_mode {self.execution_mode!r} fora do vocab")
        if self.usage.get("status") not in USAGE_STATUSES:
            raise ValueError("usage.status fora do vocab §19")

    @property
    def duration_s(self) -> float | None:
        if self.completed is None:
            return None
        return round(self.completed - self.started, 3)

    def failure_kind(self) -> str | None:
        if self.structured_output and self.structured_output.get("failure_kind"):
            return str(self.structured_output["failure_kind"])
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "spawn_id": self.spawn_id,
            "runtime": self.runtime,
            "execution_mode": self.execution_mode,
            "status": self.status,
            "started": self.started,
            "completed": self.completed,
            "duration_s": self.duration_s,
            "output": self.output,
            "structured_output": self.structured_output,
            "error": self.error,
            "usage": dict(self.usage),
            "trace_ref": self.trace_ref,
        }


def new_spawn_id(agent_id: str) -> str:
    return f"sp-{agent_id}-{uuid.uuid4().hex[:12]}"


def fingerprint_of(payload: dict[str, Any]) -> str:
    raw = repr(sorted(payload.items())).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def failed_result(
    request: AgentSpawnRequestV2,
    runtime: RuntimeName,
    *,
    mode: str,
    failure_kind: str,
    reason: str,
) -> AgentSpawnResultV2:
    """Falha nomeada — nunca sucesso vazio (§79-80, §85)."""
    if failure_kind not in FAILURE_KINDS:
        raise ValueError(f"failure_kind {failure_kind!r} fora do vocab §81")
    return AgentSpawnResultV2(
        agent_id=request.agent_id,
        spawn_id=new_spawn_id(request.agent_id),
        runtime=runtime.value,
        execution_mode=mode,
        status="failed",
        started=time.time(),
        completed=time.time(),
        error=reason,
        structured_output={"failure_kind": failure_kind},
        usage={"status": "not_available"},
    )


class BaseAdapter:
    """Contrato minimo de um runtime adapter."""

    name: RuntimeName = RuntimeName.GENERIC
    status: str = "declared"
    proof: str | None = None

    @property
    def capabilities(self) -> RuntimeCapabilities:
        from sparkforge_azure.agentic.runtime import get_capabilities

        return get_capabilities(self.name)

    def spawn_agent(self, request: AgentSpawnRequestV2) -> AgentSpawnResultV2:
        raise NotImplementedError

    def collect_result(self, spawn_id: str) -> AgentSpawnResultV2 | None:
        return None

    def tool_call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"ok": False, "failure_kind": "tool_unavailable"}
