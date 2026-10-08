---
sdd: 1
feature: DATABRICKS_UC_ADLS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/DATABRICKS_UC_ADLS/explore.md
  sha256: "21285f7d6f0092d46a358f722d219570b32deece15a4abe499c1717c52e72dda"
hypothesis:
  claim: "Compondo extractors determinísticos + governance.diagnose + regras SF-ACC + grafo de acesso + recibo, o repo diagnostica end-to-end a falha 'job Databricks não acessa tabela/path UC em ADLS' com evidência"
  prediction: "fixtures offline produzem o failure_layer esperado em cada um dos 10 cenários, com findings citando facts e unresolved explícito quando falta evidência"
  experiment: "pytest tests/test_access_pipeline.py tests/test_access_scenarios.py + sparkforge-azure diagnose"
acceptance:
  - id: AC1
    statement: "extractors offline produzem facts para storage credentials, external locations, grants, workspace bindings, catalogs/schemas/tables, RBAC assignments, ADLS ACL/network, jobs/clusters com runtime/access mode"
    verified_by: {kind: test, ref: tests/test_access_extractors.py::test_uc_artifacts_become_facts}
  - id: AC2
    statement: "scan de código reconhece abfss://, nomes UC de 3 partes, dbutils, saveAsTable/table/sql, MERGE e ops Delta"
    verified_by: {kind: test, ref: tests/test_access_extractors.py::test_notebook_scan_recognizes_uc_and_adls}
  - id: AC3
    statement: "pipeline artifacts→facts→graph→diagnose→rules→findings→failure_layer→receipt roda offline sobre um bundle"
    verified_by: {kind: test, ref: tests/test_access_pipeline.py::test_pipeline_end_to_end_offline}
  - id: AC4
    statement: "os 10 cenários determinísticos retornam o failure_layer esperado (unity_catalog, azure_rbac, adls_acl, network, workspace_binding, external_location, governance_bypass, runtime, delta_perf, unresolved)"
    verified_by: {kind: test, ref: tests/test_access_scenarios.py::test_all_scenarios_fail_at_expected_layer}
  - id: AC5
    statement: "falha de collector (401/403/rede/unsupported) vira unresolved com FailureClass, nunca 'recurso ausente'"
    verified_by: {kind: test, ref: tests/test_access_collectors.py::test_collector_failure_is_unresolved}
  - id: AC6
    statement: "metadado malicioso (comment/tag/notebook/tool result) permanece DATA_ONLY e marcado suspicious"
    verified_by: {kind: test, ref: tests/test_access_security.py::test_tainted_metadata_stays_data_only}
  - id: AC7
    statement: "CLI sparkforge-azure diagnose expõe o caso com JSON único e exit codes do contrato"
    verified_by: {kind: test, ref: tests/test_access_cli.py::test_diagnose_cli_json_contract}
success:
  - id: SC1
    metric: "pipeline completo verde offline; nenhum acesso implícito à nuvem; claims novos com prova"
    source: "pytest tests/test_access_*.py + scripts/check_claims.py"
out_of_scope:
  - "cloud write; expansão para outros serviços Azure fora do vertical"
  - "live collectors novos além de unity-catalog/rbac/adls-metadata read-only opt-in"
unknowns: []
change_kinds: [extractor, rule, rule_area, tool_or_verb, fixture_corpus]
---

# Define — DATABRICKS_UC_ADLS

O vertical conecta coleta (offline/opt-in) → facts → Graphfy → governance →
regras → findings → failure_layer → recibo. LLM nunca é a primeira camada;
ausência de evidência é `unresolved`, não `allowed`.
