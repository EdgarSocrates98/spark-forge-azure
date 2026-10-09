"""Runtime registry canonico (§20).

Expoe por runtime: adapter, capabilities (declaradas — parity.yaml),
status (provado — §7) e proof. ``capabilities.spawn_agent=True`` diz que
a plataforma oferece o mecanismo; ``status=host_proven`` so existe com
transcript/teste real gravado — hoje nenhum host tem prova, entao nada
passa de ``adapter_implemented``.
"""

from __future__ import annotations

from typing import Any

from sparkforge_azure.agentic.runtime import RuntimeName, get_capabilities

from .base import BaseAdapter
from .generic import GenericAdapter
from .host import (
    ClaudeCodeAdapter,
    DevinCLIAdapter,
    DevinDesktopAdapter,
)
from .playbook import CodexAdapter, CopilotCIAdapter

_ADAPTERS: dict[RuntimeName, type[BaseAdapter]] = {
    RuntimeName.CLAUDE_CODE: ClaudeCodeAdapter,
    RuntimeName.DEVIN_CLI: DevinCLIAdapter,
    RuntimeName.DEVIN_DESKTOP: DevinDesktopAdapter,
    RuntimeName.COPILOT_CI: CopilotCIAdapter,
    RuntimeName.CODEX: CodexAdapter,
    RuntimeName.GENERIC: GenericAdapter,
}

_INSTANCES: dict[RuntimeName, BaseAdapter] = {}


def get_adapter(runtime: RuntimeName | str) -> BaseAdapter:
    """Resolve o adapter de um runtime — closed set, fail-closed."""
    name = runtime if isinstance(runtime, RuntimeName) else RuntimeName(runtime)
    if name not in _INSTANCES:
        _INSTANCES[name] = _ADAPTERS[name]()
    return _INSTANCES[name]


def runtime_registry() -> dict[RuntimeName, dict[str, Any]]:
    """§20 — runtime → adapter → capabilities → status → proof."""
    out: dict[RuntimeName, dict[str, Any]] = {}
    for name, cls in _ADAPTERS.items():
        adapter = get_adapter(name)
        out[name] = {
            "adapter": f"{cls.__module__}.{cls.__name__}",
            "capabilities": vars(get_capabilities(name)),
            "status": adapter.status,
            "proof": adapter.proof,
        }
    return out
