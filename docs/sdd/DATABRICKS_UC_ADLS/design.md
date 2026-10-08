---
sdd: 1
feature: DATABRICKS_UC_ADLS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/DATABRICKS_UC_ADLS/define.md
  sha256: "f6af5a17645fb25e319c4ed5746af73fa44a5e36700e1744dd410760a3559729"
files:
  - {path: sparkforge_azure/azure/casefile.py, action: create, reason: "modelo de bundle: caso + artefatos (UC exports, RBAC, ACLs, network, workspace) → scenario normalizado para governance.diagnose"}
  - {path: sparkforge_azure/azure/extract.py, action: create, reason: "extractors offline: storage credentials, external locations, grants, bindings, catalogs/schemas/tables, role assignments, ACLs, network"}
  - {path: sparkforge_azure/azure/pipeline.py, action: create, reason: "artifacts→facts→access graph→governance.diagnose→regras→findings→failure_layer→receipt"}
  - {path: sparkforge_azure/azure/receipt.py, action: create, reason: "execution receipt: case/profile/tools/sources/facts/rules/findings/agents/budget/unresolved"}
  - {path: sparkforge_azure/facts/notebook_scan.py, action: create, reason: "scan de código/notebook: abfss://, nomes UC 3 partes, dbutils, saveAsTable/table/sql, MERGE, Delta ops"}
  - {path: sparkforge_azure/collectors/unity_catalog.py, action: create, reason: "collector UC read-only opt-in (live) + ingest de exports"}
  - {path: sparkforge_azure/collectors/azure_rbac.py, action: create, reason: "collector de role assignments: export ou Azure SDK opt-in; falhas viram unresolved"}
  - {path: sparkforge_azure/collectors/adls_meta.py, action: create, reason: "collector de ACLs/network do ADLS: export ou SDK opt-in; falhas viram unresolved"}
  - {path: sparkforge_azure/collectors/failure.py, action: create, reason: "mapeia exceções de SDK→FailureClass (authn/authz/network/rate/provider/invalid/missing)"}
  - {path: rules/catalog/azure_access.yaml, action: create, reason: "áreas SFA-UC/SFA-ADLS/SFA-ID/SFA-NET/SFA-DBR/SFA-DELTA"}
  - {path: sparkforge_azure/cli/cmd_diagnose.py, action: create, reason: "sparkforge-azure diagnose --bundle/--scenario"}
  - {path: sparkforge_azure/cli/main.py, action: modify, reason: "registrar cmd_diagnose"}
  - {path: sparkforge_azure/mcp/access_tools.py, action: create, reason: "sfa_diagnose_access (READ_ONLY, offline artifacts)"}
  - {path: sparkforge_azure/mcp/tools.py, action: modify, reason: "TOOL_MODULES += access_tools"}
  - {path: tests/test_access_extractors.py, action: create, reason: "extractors → facts"}
  - {path: tests/test_access_pipeline.py, action: create, reason: "pipeline end-to-end + evidence path"}
  - {path: tests/test_access_scenarios.py, action: create, reason: "10 cenários com failure_layer esperado"}
  - {path: tests/test_access_collectors.py, action: create, reason: "falhas de collector → unresolved"}
  - {path: tests/test_access_security.py, action: create, reason: "taint/DATA_ONLY"}
  - {path: tests/test_access_cli.py, action: create, reason: "contrato CLI"}
  - {path: fixtures/access/, action: create, reason: "bundles de caso para os 10 cenários"}
decisions:
  - id: D1
    choice: "reusar governance.diagnose como motor de camadas; pipeline.py só monta Scenario a partir de facts"
    rejected: ["reescrever a lógica de camadas: duplicação sem ganho"]
    rollback: "chamar diagnose direto com Scenario manual"
  - id: D2
    choice: "collectors live opt-in via SDK extras; offline default via exports JSON"
    rejected: ["live implícito se credenciais existem: viola offline-first"]
    rollback: "remover caminho live, manter exports"
  - id: D3
    choice: "failure_layer é vocabulário próprio derivado do layer result, não o nome interno do layer"
    rejected: ["expor layer interno direto: acopla vocabulário do público a nomes internos"]
    rollback: "mapa 1:1"
covers:
  - {part: extractors, acceptance: [AC1, AC2]}
  - {part: pipeline, acceptance: [AC3, AC4]}
  - {part: collectors, acceptance: [AC5]}
  - {part: security, acceptance: [AC6]}
  - {part: cli-mcp, acceptance: [AC7]}
---

# Design — DATABRICKS_UC_ADLS

`casefile.py` valida o bundle; `extract.py` normaliza artefatos em `Fact`;
`pipeline.py` monta `Scenario`, roda `diagnose`, aplica regras `azure_access`
sobre os facts, constrói grafo de acesso para caminho de evidência, mapeia o
primeiro DENY/UNKNOWN para `failure_layer` público e emite receipt.
