"""Host adapters — claude_code / devin_cli / devin_desktop (§87-90).

Honestidade §9/§88: o adapter existe e sabe montar a linha de comando do
host, mas sem transcript/teste de host o status fica
``adapter_implemented`` — nunca ``host_proven``.

Execucao real exige opt-in explicito (§199 — nada roda em background
silencioso): ``SPARKFORGE_AZURE_HOST_EXECUTION=1``. Sem o opt-in, ou sem
o binario no PATH, ``spawn_agent`` devolve ``runtime_unavailable``
nomeado — nunca finge sucesso (§79).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

from sparkforge_azure.agentic.runtime import RuntimeName

from .base import (
    AgentSpawnRequestV2,
    AgentSpawnResultV2,
    BaseAdapter,
    failed_result,
    fingerprint_of,
    new_spawn_id,
)

_OPT_IN = "SPARKFORGE_AZURE_HOST_EXECUTION"


def _opted_in() -> bool:
    return os.environ.get(_OPT_IN) == "1"


class HostCLIAdapter(BaseAdapter):
    """Adapter que despacha para o CLI do host quando ele existe.

    Subclasses definem ``binary`` e ``argv_for``. O subprocesso recebe a
    task materializada e um timeout — sem retry automatico (§206).
    """

    status = "adapter_implemented"
    binary = ""
    execution_mode = "subagent"

    def argv_for(self, request: AgentSpawnRequestV2) -> list[str]:
        return [self.binary, "--print", request.task]

    def spawn_agent(self, request: AgentSpawnRequestV2) -> AgentSpawnResultV2:
        if not self.binary or shutil.which(self.binary) is None:
            return failed_result(
                request, self.name,
                mode="inline",
                failure_kind="runtime_unavailable",
                reason=f"runtime_unavailable: {self.binary or 'host'} nao esta no PATH",
            )
        if not _opted_in():
            return failed_result(
                request, self.name,
                mode="inline",
                failure_kind="runtime_unavailable",
                reason=(
                    "runtime_unavailable: host execution exige "
                    f"{_OPT_IN}=1 (§199 — sem execucao implicita)"
                ),
            )
        return self._run_host(request)

    def _run_host(self, request: AgentSpawnRequestV2) -> AgentSpawnResultV2:
        started = time.time()
        spawn_id = new_spawn_id(request.agent_id)
        try:
            proc = subprocess.run(  # noqa: S603 - argv fixo por adapter,
                self.argv_for(request),  # opt-in explicito (§199)
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return AgentSpawnResultV2(
                agent_id=request.agent_id,
                spawn_id=spawn_id,
                runtime=self.name.value,
                execution_mode=self.execution_mode,
                status="unresolved",
                started=started,
                completed=time.time(),
                error="timeout",
                structured_output={"failure_kind": "timeout"},
            )
        except OSError as exc:
            return failed_result(
                request, self.name,
                mode=self.execution_mode,
                failure_kind="spawn_failed",
                reason=f"spawn_failed: {exc}",
            )
        trace = fingerprint_of({
            "spawn_id": spawn_id,
            "rc": proc.returncode,
            "stdout": proc.stdout[:4096],
        })
        if proc.returncode != 0:
            return AgentSpawnResultV2(
                agent_id=request.agent_id,
                spawn_id=spawn_id,
                runtime=self.name.value,
                execution_mode=self.execution_mode,
                status="failed",
                started=started,
                completed=time.time(),
                error=f"spawn_failed: rc={proc.returncode}",
                structured_output={"failure_kind": "spawn_failed"},
                trace_ref=trace,
            )
        # Output de host e DATA_ONLY — o caller valida o schema (§29-31).
        return AgentSpawnResultV2(
            agent_id=request.agent_id,
            spawn_id=spawn_id,
            runtime=self.name.value,
            execution_mode=self.execution_mode,
            status="completed",
            started=started,
            completed=time.time(),
            output=proc.stdout,
            usage={"status": "unresolved"},
            trace_ref=trace,
        )


class ClaudeCodeAdapter(HostCLIAdapter):
    name = RuntimeName.CLAUDE_CODE
    binary = "claude"

    def argv_for(self, request: AgentSpawnRequestV2) -> list[str]:
        return [
            self.binary, "-p", request.task,
            "--output-format", "json",
        ]


class DevinCLIAdapter(HostCLIAdapter):
    name = RuntimeName.DEVIN_CLI
    binary = "devin"


class DevinDesktopAdapter(HostCLIAdapter):
    name = RuntimeName.DEVIN_DESKTOP
    binary = "devin-desktop"
