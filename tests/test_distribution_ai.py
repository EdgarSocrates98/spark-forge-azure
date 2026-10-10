"""`sparkforge-azure ai` — the open-host flow, every step injectable.

Without injected `which`/`runner`/`exec_host` the test never reaches a real
binary, version, auth or process: `host_state` returns NOT_DETECTED and
`ai_flow` never launches.
"""
from __future__ import annotations

import json

from sparkforge_azure.distribution import ai as open_host
from sparkforge_azure.install import service as install_service


def _which_fake(presentes: dict[str, str]):
    return lambda nome: presentes.get(nome)


def _runner_fake(saidas: dict[tuple[str, ...], tuple[int, str]]):
    def run(argv):
        chave = tuple(argv[1:])
        assert chave in saidas, f"unexpected argv: {argv}"
        return saidas[chave]
    return run


def _status(monkeypatch, **kw):
    base = {"status": "unverified", "checks": []}
    base.update(kw)
    monkeypatch.setattr(install_service, "status", lambda **_k: base)


def test_host_ausente_e_not_detected(tmp_path):
    estado = open_host.host_state(
        "devin", repo=tmp_path, which=lambda _n: None,
        runner=lambda _a: (_ for _ in ()).throw(AssertionError("chamou")),
    )
    assert estado["state"] == "NOT_DETECTED"
    assert "binary_path" not in estado


def test_fluxo_completo_ate_ready(tmp_path, monkeypatch):
    _status(monkeypatch, status="healthy",
            checks=[{"id": "distribution.status", "status": "PASS"}])
    saidas = {
        ("--version",): (0, "devin 3000.11.3 (abc)\n"),
        ("auth", "status"): (0, "Logged in (via Devin).\nCredentials:\n  File: /x/segredo.toml"),
    }
    estado = open_host.host_state(
        "devin", repo=tmp_path,
        which=_which_fake({"devin": "/bin/devin"}),
        runner=_runner_fake(saidas),
    )
    assert estado["state"] == "READY"
    assert estado["version"] == "devin 3000.11.3 (abc)"
    assert estado["logged_in"] is True
    # nenhum caminho de credencial vaza para o recibo
    assert "segredo" not in json.dumps(estado)
    assert estado["integration"]["state"] == "healthy"


def test_deslogado_nao_lanca_e_aponta_login(tmp_path, monkeypatch):
    _status(monkeypatch)
    saidas = {
        ("--version",): (0, "codex-cli 0.160.0"),
        ("login", "status"): (0, "Not logged in"),
    }
    lancou = []
    recibo = open_host.ai_flow(
        "codex", repo=tmp_path, launch=True, tty=True,
        which=_which_fake({"codex": "/bin/codex"}),
        runner=_runner_fake(saidas),
        exec_host=lambda _c, _r: lancou.append(True) or 0,
    )
    assert recibo["launched"] is False
    assert recibo["launch_refused"] == "login_required"
    assert recibo["login_hint"] == "codex login"
    assert lancou == []
    assert recibo["hosts"][0]["state"] == "NEEDS_LOGIN"


def test_sem_tty_recusa_mas_traz_comando(tmp_path, monkeypatch):
    _status(monkeypatch, status="healthy")
    saidas = {
        ("--version",): (0, "2.1.295 (Claude Code)"),
        ("auth", "status"): (0, json.dumps({"loggedIn": True})),
    }
    recibo = open_host.ai_flow(
        "claude", repo=tmp_path, launch=True, tty=False,
        which=_which_fake({"claude": "/bin/claude"}),
        runner=_runner_fake(saidas),
        exec_host=lambda _c, _r: 0,
    )
    assert recibo["launched"] is False
    assert recibo["launch_refused"] == "no_tty"
    assert recibo["hosts"][0]["launch_command"] == "claude"


def test_com_tty_lanca_no_repo_e_registra_exit(tmp_path, monkeypatch):
    _status(monkeypatch, status="healthy")
    chamadas = []
    saidas = {
        ("--version",): (0, "devin 3000.11.3 (abc)"),
        ("auth", "status"): (0, "Logged in (via Devin)."),
    }

    def exec_fake(caminho, cwd):
        chamadas.append((caminho, cwd))
        return 0
    recibo = open_host.ai_flow(
        "devin", repo=tmp_path, launch=True, tty=True,
        which=_which_fake({"devin": "/bin/devin"}),
        runner=_runner_fake(saidas),
        exec_host=exec_fake,
    )
    assert recibo["launched"] is True
    assert recibo["host_exit_code"] == 0
    assert chamadas == [("/bin/devin", tmp_path)]


def test_all_mede_os_tres_e_nunca_lanca(tmp_path, monkeypatch):
    _status(monkeypatch)
    recibo = open_host.ai_flow(
        "all", repo=tmp_path, launch=True,
        which=lambda _n: None,
        runner=lambda _a: (_ for _ in ()).throw(AssertionError("chamou")),
        exec_host=lambda _c, _r: (_ for _ in ()).throw(AssertionError("lancou")),
    )
    assert recibo["launched"] is False
    assert recibo["launch_refused"].startswith("selector")
    assert [h["host"] for h in recibo["hosts"]] == list(open_host.HOST_NAMES)
    assert all(h["state"] == "NOT_DETECTED" for h in recibo["hosts"])


def test_host_desconhecido_recusa_com_nome(tmp_path):
    estado = open_host.host_state("copilot", repo=tmp_path)
    assert estado["state"] == "refused"
    assert estado["reason"] == "host_unknown"
