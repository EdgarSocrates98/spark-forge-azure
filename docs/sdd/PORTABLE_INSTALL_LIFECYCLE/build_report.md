---
sdd: 1
feature: PORTABLE_INSTALL_LIFECYCLE
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/PORTABLE_INSTALL_LIFECYCLE/plan.md
  sha256: "a2ea74e45dd2ba51cb5c18c6fa0be5ecee34ac21f635cb8b7d6fd64f4a7087b6"
tasks:
  - id: T1
    status: done
    red: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_install_lifecycle.py -q", exit: 0}
claims:
  - text: "dry-run emite forge/InstallReceipt/v1 status=planned com planned_files e nao escreve nada"
    evidence_ref: "tests/test_install_lifecycle.py::test_dry_run_plans_and_writes_nothing"
  - text: "apply exige --yes (FORGE-INSTALL-PLAN-NOT-APPROVED); profile desconhecido e host desconhecido recusam"
    evidence_ref: "tests/test_install_lifecycle.py::test_install_without_yes_is_refused"
  - text: "apply escreve project.yaml + mcp key + marcadores + espelhos de skills ledgerados; chaves estrangeiras de .mcp.json preservadas"
    evidence_ref: "tests/test_install_lifecycle.py::test_install_apply_writes_managed_assets"
  - text: "status/doctor emitem forge/InstallationHealth/v1; doctor traz o check mcp-handshake honesto (BLOCKED quando CLI ausente)"
    evidence_ref: "tests/test_install_lifecycle.py::test_status_and_doctor_health_schema"
  - text: "repair restaura drift do ledger; --dry-run lista drift sem tocar"
    evidence_ref: "tests/test_install_lifecycle.py::test_repair_restores_drifted_managed"
  - text: "uninstall remove so o ledgerado, poda diretorios esvaziados, preserva conteudo do usuario; no-op em raiz virgem"
    evidence_ref: "tests/test_install_lifecycle.py::test_uninstall_removes_managed_preserves_user"
  - text: "--scope user escreve assets de host sob ~ sem identidade de projeto"
    evidence_ref: "tests/test_install_lifecycle.py::test_user_scope_writes_under_home"
  - text: "install esta no parser com 7 ops, na surface.lock e na referencia de CLI"
    evidence_ref: "tests/test_install_lifecycle.py::test_cli_dispatches_all_verbs"
change_id: "feat/portable-installation"
---

# Build Report — PORTABLE_INSTALL_LIFECYCLE

Red registrado: `tests/test_install_lifecycle.py` rodado sem a
implementação (`sparkforge_azure/install` + `cmd_install` movidos para
fora do pacote) falha na coleta com `ModuleNotFoundError` — exit 2,
cobrindo todos os ACs do arquivo.

Defeitos reais pegos pelo build durante a sessão:

- `test_repair_restores_drifted_managed` falhou — `assess_ledger` usa
  `present` como estado sadio, não `ok`; repair agora filtra
  `state != "present"`.
- `test_install_without_yes_is_refused` falhou — `PortableError`
  valida `kind` contra `FAILURE_KINDS`; os 13 kinds canônicos
  `FORGE-INSTALL-*` entraram no vocabulário fechado
  (`distribution/errors.py`), o ponto de extensão documentado.
- `test_uninstall_removes_managed_preserves_user` falhou — `detach`
  remove arquivos mas não poda diretórios esvaziados; `uninstall`
  chama `_prune_empty_dirs` do installkit após o detach.
- Handshake MCP reportava `FAIL` para CLI ausente do PATH — corrigido
  no canonical do the-forge para `BLOCKED` e re-vendored aos 7 repos
  (hash-parity verificada).
- `check_surface_lock.py` reprovou `install` ausente — lock
  regenerado via `--update`.
