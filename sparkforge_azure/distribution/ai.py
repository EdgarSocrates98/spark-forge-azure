"""``sparkforge-azure ai`` — observe the AI host, open it when supported.

Real per-host flow, every step a documented command verified against the
installed versions (devin 3000.11.3, Claude Code 2.1.295, codex-cli
0.160.0, read in 2026-10):

1. detect the binary (``shutil.which``);
2. read the version (``<bin> --version``);
3. check authentication through the official status subcommand — the
   receipt carries only the ``logged_in`` boolean, never the output (it
   can list credential paths);
4. read the repo's integration state (``install.status`` → distribution
   status);
5. with ``--launch`` and a TTY, run ``<bin>`` in the repo directory — the
   host REPL inherits the terminal and returns its exit code to the
   receipt. Without TTY or ``--launch``, the receipt carries
   ``launch_command`` for the operator to paste.

A signed-out host is never launched: the receipt points at the official
login command and never asks for a credential in a prompt.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Which = Callable[[str], str | None]
Runner = Callable[[list[str]], tuple[int, str]]

_TIMEOUT_S = 15
_SAIDA_MAX = 400

LOGIN_HINTS = {
    "devin": "devin auth login",
    "claude": "claude auth login",
    "codex": "codex login",
}

#: Hosts the flow knows how to observe. Order follows distribution.hosts.
HOST_NAMES: tuple[str, ...] = ("claude", "devin", "codex")


@dataclass(frozen=True)
class _HostCmd:
    binary: str
    auth_status: tuple[str, ...] | None


_HOST_CMDS = {
    "claude": _HostCmd("claude", ("auth", "status")),
    "devin": _HostCmd("devin", ("auth", "status")),
    "codex": _HostCmd("codex", ("login", "status")),
}


def _default_which(binary: str) -> str | None:
    return shutil.which(binary)


def _default_runner(argv: list[str]) -> tuple[int, str]:
    proc = subprocess.run(  # noqa: S603
        argv, capture_output=True, text=True, timeout=_TIMEOUT_S, errors="replace"
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _logged_in(host: str, saida: str) -> bool | None:
    """Only the boolean. No legible positive/negative evidence → ``None`` (honest)."""
    if host == "claude":
        try:
            dados = json.loads(saida)
        except ValueError:
            dados = None
        if isinstance(dados, dict) and "loggedIn" in dados:
            return bool(dados["loggedIn"])
    low = saida.lower()
    # negative before positive: "Not logged in" contains "logged in"
    if any(trecho in low for trecho in (
        "not logged", "logged out", "no credentials", "unauthorized",
    )):
        return False
    if "logged in" in low:
        return True
    return None


def _chamar(executavel: str, argv: list[str], runner: Runner) -> tuple[int, str] | dict[str, Any]:
    try:
        return runner([executavel, *argv])
    except subprocess.TimeoutExpired as erro:
        return {
            "status": "refused",
            "reason": "host_cli_timeout",
            "command": " ".join(argv),
            "timeout_s": erro.timeout,
        }
    except OSError as erro:
        return {
            "status": "refused",
            "reason": "host_cli_failed",
            "command": " ".join(argv),
            "output": str(erro)[-_SAIDA_MAX:],
        }


def _integracao(repo: Path) -> dict[str, Any]:
    """Repo install state, touching nothing — ``unverified`` when never installed."""
    try:
        from sparkforge_azure.install import service

        st = service.status(scope="project", root=repo)
    except Exception as erro:  # status must never take the host flow down
        return {"state": "unknown", "error": str(erro)[:200]}
    return {
        "state": st.get("status", "unknown"),
        "checks": [
            {"id": c.get("id"), "status": c.get("status")}
            for c in (st.get("checks") or [])
        ],
    }


def host_state(
    host: str,
    *,
    repo: Path,
    which: Which | None = None,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Observed state of one host: binary, version, auth, integration, launch cmd."""
    if host not in _HOST_CMDS:
        return {"host": host, "state": "refused",
                "reason": "host_unknown", "known": list(_HOST_CMDS)}
    which = which or _default_which
    runner = runner or _default_runner
    cmd = _HOST_CMDS[host]
    estado: dict[str, Any] = {
        "host": host,
        "binary": cmd.binary,
        "launch_command": cmd.binary,
    }
    caminho = which(cmd.binary)
    if not caminho:
        estado["state"] = "NOT_DETECTED"
        return estado
    estado["binary_path"] = caminho
    estado["state"] = "DETECTED"

    versao = _chamar(caminho, ["--version"], runner)
    if isinstance(versao, dict):
        estado["version_refused"] = versao
    else:
        rc, saida = versao
        primeira = next(
            (linha.strip() for linha in saida.splitlines() if linha.strip()), "")
        estado["version"] = primeira or None
        estado["state"] = "SUPPORTED" if rc == 0 else "DETECTED"

    if cmd.auth_status is None:
        estado["logged_in"] = None
        estado["auth_note"] = "no documented status subcommand in this revision"
    else:
        auth = _chamar(caminho, list(cmd.auth_status), runner)
        if isinstance(auth, dict):
            estado["auth_refused"] = auth
            estado["logged_in"] = None
        else:
            estado["logged_in"] = _logged_in(host, auth[1])
    if estado.get("logged_in") is False:
        estado["login_hint"] = LOGIN_HINTS.get(host)

    estado["integration"] = _integracao(repo)
    estado["state"] = _estado_final(estado)
    return estado


def _estado_final(estado: dict[str, Any]) -> str:
    if estado.get("logged_in") is False:
        return "NEEDS_LOGIN"
    integ = (estado.get("integration") or {}).get("state")
    if integ == "healthy":
        return "READY"
    if integ in {"degraded", "broken"}:
        return "INTEGRATION_" + integ.upper()
    return "SUPPORTED"


def ai_flow(
    alvo: str,
    *,
    repo: Path,
    launch: bool = False,
    tty: bool | None = None,
    which: Which | None = None,
    runner: Runner | None = None,
    exec_host: Callable[[str, Path], int] | None = None,
) -> dict[str, Any]:
    """The §3.2 flow: implicit selector via ``alvo`` (``all`` measures every
    declared host), per-host state, and a real launch when ``--launch`` +
    TTY + READY.

    ``exec_host(caminho, repo)`` is the launch seam — the CLI injects
    ``subprocess.call``; a test injects a spy. Without a TTY, ``launched``
    is false and ``launch_refused`` says why — never silence."""
    repo = Path(repo)
    nomes = list(HOST_NAMES) if alvo == "all" else [alvo]
    estados = [
        host_state(nome, repo=repo, which=which, runner=runner)
        for nome in nomes
    ]
    recibo: dict[str, Any] = {
        "repo": repo.as_posix(),
        "hosts": estados,
        "launched": False,
    }
    if alvo == "all" or not launch:
        if launch:
            recibo["launch_refused"] = "selector `all` does not launch: pick one host"
        return recibo

    estado = estados[0]
    tty = sys.stdin.isatty() if tty is None else tty
    if estado["state"] == "NOT_DETECTED":
        recibo["launch_refused"] = "host_absent"
    elif estado["state"] == "NEEDS_LOGIN":
        recibo["launch_refused"] = "login_required"
        recibo["login_hint"] = estado.get("login_hint")
    elif not tty:
        recibo["launch_refused"] = "no_tty"
    else:
        # Path came from shutil.which — same trust level as any PATH exec.
        exec_fn = exec_host or (
            lambda caminho, cwd: subprocess.call(  # noqa: S603
                [caminho], cwd=str(cwd)))
        recibo["launched"] = True
        recibo["host_exit_code"] = exec_fn(estado["binary_path"], repo)
    return recibo
