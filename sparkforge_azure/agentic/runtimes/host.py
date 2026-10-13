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

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

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

#: repo root a partir deste modulo (sparkforge_azure/agentic/runtimes/).
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _opted_in() -> bool:
    return os.environ.get(_OPT_IN) == "1"


def _valid_proof(record: dict) -> bool:
    """§9 — prova = transcript real: completed + trace_ref sha256."""
    return (
        isinstance(record, dict)
        and record.get("status") == "completed"
        and str(record.get("trace_ref") or "").startswith("sha256:")
    )


class HostCLIAdapter(BaseAdapter):
    """Adapter que despacha para o CLI do host quando ele existe.

    Subclasses definem ``binary`` e ``argv_for``. O subprocesso recebe a
    task materializada e um timeout — sem retry automatico (§206).

    ``status`` deriva de ``evals/host_proof/<runtime>.json``: transcript
    valido promove a ``host_proven``; ausente/invalido nunca promove (§9).
    """

    binary = ""
    execution_mode = "subagent"

    def _proof_dir(self) -> Path:
        return _REPO_ROOT / "evals" / "host_proof"

    def _proof_artifact(self) -> dict | None:
        path = self._proof_dir() / f"{self.name.value}.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    @property
    def status(self) -> str:
        rec = self._proof_artifact()
        return "host_proven" if _valid_proof(rec) else "adapter_implemented"

    @property
    def proof(self) -> str | None:
        rec = self._proof_artifact()
        if not _valid_proof(rec):
            return None
        return f"evals/host_proof/{self.name.value}.json"

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
        output, usage = self.postprocess(proc.stdout)
        # Output de host e DATA_ONLY — o caller valida o schema (§29-31).
        return AgentSpawnResultV2(
            agent_id=request.agent_id,
            spawn_id=spawn_id,
            runtime=self.name.value,
            execution_mode=self.execution_mode,
            status="completed",
            started=started,
            completed=time.time(),
            output=output,
            usage=usage,
            trace_ref=trace,
        )

    def postprocess(self, stdout: str) -> tuple[str, dict]:
        """Extrai o texto do modelo e o uso observado do stdout do host.

        Default: stdout cru + usage ``unresolved``. Adapters com envelope
        estruturado (claude --output-format json) sobrescrevem e medem
        de verdade — ``measured`` so quando o envelope informa.
        """
        return stdout, {"status": "unresolved"}


class ClaudeCodeAdapter(HostCLIAdapter):
    name = RuntimeName.CLAUDE_CODE
    binary = "claude"

    def argv_for(self, request: AgentSpawnRequestV2) -> list[str]:
        return [
            self.binary, "-p", request.task,
            "--output-format", "json",
        ]

    def postprocess(self, stdout: str) -> tuple[str, dict]:
        """Envelope `claude --output-format json`: result + usage reais."""
        try:
            env = json.loads(stdout)
        except json.JSONDecodeError:
            return stdout, {"status": "unresolved"}
        usage_raw = env.get("usage") or {}
        usage: dict = {"status": "unresolved"}
        if "input_tokens" in usage_raw or env.get("total_cost_usd") is not None:
            usage = {
                "status": "measured",
                "input_tokens": usage_raw.get("input_tokens"),
                "output_tokens": usage_raw.get("output_tokens"),
                "cache_creation_input_tokens": usage_raw.get(
                    "cache_creation_input_tokens"),
                "cost_usd": env.get("total_cost_usd"),
                "model": next(iter(env.get("modelUsage") or {}), None),
            }
        return str(env.get("result") or stdout), usage


class DevinCLIAdapter(HostCLIAdapter):
    name = RuntimeName.DEVIN_CLI
    binary = "devin"


class DevinDesktopAdapter(HostCLIAdapter):
    name = RuntimeName.DEVIN_DESKTOP
    binary = "devin-desktop"
