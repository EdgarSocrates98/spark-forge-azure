---
sdd: 1
feature: DATABRICKS_UC_ADLS
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/DATABRICKS_UC_ADLS/plan.md
  sha256: "54a4fc5ae8d98e7918aa5f0d76a3e2b98cc914c858c09fcdc054896dee60b2fe"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-base-red && ../.venv/Scripts/python -m pytest tests/test_access_extractors.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_extractors.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-base-red && ../.venv/Scripts/python -m pytest tests/test_access_extractors.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_extractors.py::test_notebook_scan_recognizes_uc_and_adls -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-base-red && ../.venv/Scripts/python -m pytest tests/test_access_pipeline.py tests/test_access_scenarios.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_pipeline.py tests/test_access_scenarios.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-base-red && ../.venv/Scripts/python -m pytest tests/test_access_collectors.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_collectors.py -q", exit: 0}
  - id: T5
    status: done
    red: {command: "cd .tmp-base-red && ../.venv/Scripts/python -m pytest tests/test_access_security.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_security.py -q", exit: 0}
  - id: T6
    status: done
    red: {command: "cd .tmp-base-red && ../.venv/Scripts/python -m pytest tests/test_access_cli.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_access_cli.py -q", exit: 0}
claims:
  - text: "pipeline offline bundle→facts→access_graph→governance.diagnose→rules→findings→failure_layer→receipt roda sem nuvem"
    evidence_ref: "tests/test_access_pipeline.py::test_pipeline_end_to_end_offline"
  - text: "10 cenários determinísticos produzem o failure_layer esperado do vocabulário público"
    evidence_ref: "tests/test_access_scenarios.py::test_all_scenarios_fail_at_expected_layer"
  - text: "falha de collector (403/rede/SDK ausente) vira unresolved com FailureClass"
    evidence_ref: "tests/test_access_collectors.py::test_collector_failure_is_unresolved"
  - text: "metadado hostil em artefato permanece DATA_ONLY e marcado suspicious no trust scan"
    evidence_ref: "tests/test_access_security.py"
  - text: "sparkforge-azure diagnose emite um JSON e honra exit 0/1/2; sfa_diagnose_access expõe o mesmo pipeline via MCP read-only"
    evidence_ref: "tests/test_access_cli.py"
change_id: "feat/cycle2-evolution"
---

# Build Report — DATABRICKS_UC_ADLS

Reds registrados num worktree da base (`b1caf70`): os seis arquivos de teste
novos falham na coleta (exit 2 — `azure.casefile`, `azure.pipeline`,
`facts.notebook_scan`, `collectors.unity_catalog` etc. não existiam).

- `pytest tests/test_access_*.py -q` → 23 passed.
- `sparkforge-azure diagnose --bundle tests/fixtures/access/s01_uc_privilege_denied`
  → JSON completo, exit 1, `failure_layer: unity_catalog`.
- Surface lock regenerado: `diagnose`, `collect unity-catalog|azure-rbac|adls-meta`,
  tool `sfa_diagnose_access` (READ_ONLY, compact).
- `CliError` movido para `sparkforge_azure/cli/__init__.py`: sob
  `python -m sparkforge_azure.cli.main` o módulo era importado duas vezes
  (`__main__` + nome canônico) e `except CliError` não capturava — bug real
  corrigido nesta onda.
- `collectors/failure.py` classifica exceções em FailureClass; collectors live
  retornam `unresolved` em vez de levantar (ou de fingir ausência de recurso).
- `rules/catalog/azure_access.yaml`: 4 regras SF-ACC avaliadas pelo engine;
  findings estruturais SF-ACC-010/011/012 (bypass, delta path, runtime legacy)
  são emitidos pelo pipeline porque correlacionam o Diagnosis inteiro.
- Conflicto `uc_permission_exists_storage_credential_fails` propositalmente fora
  do mapa de failure_layer: ele dispara para qualquer deny de storage, então o
  root cause da chain é o layer honesto.
