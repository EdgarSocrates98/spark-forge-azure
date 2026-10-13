---
sdd: 1
feature: PORTABLE_INSTALL_LIFECYCLE
phase: define
profile: dev
status: done
hypothesis:
  claim: "O verbo `sparkforge-azure install` expõe o ciclo de vida do contrato forge/* (apply/status/doctor/repair/uninstall/update/mcp-verify) sobre o ledger do distribution sem duplicá-lo, com recibos forge/InstallReceipt/v1 e saúde forge/InstallationHealth/v1 idênticos aos irmãos"
  prediction: "dry-run planeja sem escrever; apply exige --yes; drift em asset gerenciado é reparado; uninstall remove só o ledgerado e poda diretórios vazios preservando conteúdo do usuário"
  experiment: "pytest tests/test_install_lifecycle.py (16 testes)"
acceptance:
  - id: AC1
    statement: "--dry-run emite forge/InstallReceipt/v1 status=planned com planned_files e zero mutação no target"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_dry_run_plans_and_writes_nothing}
  - id: AC2
    statement: "apply sem --yes recusa FORGE-INSTALL-PLAN-NOT-APPROVED; profile desconhecido recusa"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_install_without_yes_is_refused}
  - id: AC3
    statement: "apply --yes escreve project.yaml + mcp key + marcadores + espelhos de skills ledgerados; chaves estrangeiras de .mcp.json preservadas; profile minimal não instala espelhos"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_install_apply_writes_managed_assets}
  - id: AC4
    statement: "status e doctor emitem forge/InstallationHealth/v1; doctor inclui check mcp-handshake honesto"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_status_and_doctor_health_schema}
  - id: AC5
    statement: "repair restaura asset ledgerado modificado e reporta drift em --dry-run sem tocar"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_repair_restores_drifted_managed}
  - id: AC6
    statement: "uninstall remove só o ledgerado, poda diretórios esvaziados, preserva conteúdo do usuário e é no-op em raiz virgem"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_uninstall_removes_managed_preserves_user}
  - id: AC7
    statement: "--scope user escreve só assets de host sob ~ (sem identidade de projeto), incluindo espelhos de skills"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_user_scope_writes_under_home}
  - id: AC8
    statement: "o verbo install aparece no parser com os 7 ops e entra na surface.lock + referência de CLI"
    verified_by: {kind: test, ref: tests/test_install_lifecycle.py::test_cli_dispatches_all_verbs}
success:
  - id: SC1
    metric: "16 testes verdes + gates do repo (ruff, surface lock, docs surface, portability, claims)"
    source: "pytest + scripts/check_*.py"
out_of_scope:
  - "reescrita do ledger do distribution (adotado como está)"
  - "install no escopo workspace instalando em todos os membros (Phase 7 do programa)"
  - "MCP server runtime hardening além do handshake (Phase 8)"
unknowns: []
change_kinds: [tool_or_verb]
---

# Define — PORTABLE_INSTALL_LIFECYCLE

O sibling AWS já tem `sparkforge-aws install`; api-forge e the-forge
também. Azure tinha a máquina de ownership mais rica (ledger +
hostfiles + detach) mas nenhuma surface `install` — esta feature
adota o contrato `forge/*` sobre o que já existe, sem duplicar ledger.
