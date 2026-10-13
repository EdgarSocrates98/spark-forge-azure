"""Runtime adapters — boundary §11-22 do agent runtime wave."""

from sparkforge_azure.agentic.runtimes.base import (
    EXECUTION_MODES,
    FAILURE_KINDS,
    RUNTIME_STATUSES,
    USAGE_STATUSES,
    AgentSpawnRequestV2,
    AgentSpawnResultV2,
    BaseAdapter,
)
from sparkforge_azure.agentic.runtimes.registry import (
    get_adapter,
    runtime_registry,
)

__all__ = [
    "EXECUTION_MODES",
    "FAILURE_KINDS",
    "RUNTIME_STATUSES",
    "USAGE_STATUSES",
    "AgentSpawnRequestV2",
    "AgentSpawnResultV2",
    "BaseAdapter",
    "get_adapter",
    "runtime_registry",
]
