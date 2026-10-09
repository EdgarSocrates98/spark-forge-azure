"""Playbook adapter — floor para hosts sem spawn real (§15-16).

codex/copilot_ci nao tem subagent provado: a role executa via o mesmo
conjunto de executores deterministicos do INLINE, mas o
``execution_mode`` reportado e ``playbook`` — nunca contado como
``spawned_agents`` (§16).
"""

from __future__ import annotations

from sparkforge_azure.agentic.runtime import RuntimeName

from .generic import InlineAdapter


class PlaybookAdapter(InlineAdapter):
    """Copilot CI / Codex: mesmo executor deterministico, modo playbook."""

    execution_mode = "playbook"


class CodexAdapter(PlaybookAdapter):
    name = RuntimeName.CODEX


class CopilotCIAdapter(PlaybookAdapter):
    name = RuntimeName.COPILOT_CI
