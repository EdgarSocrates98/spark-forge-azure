---
sdd: 1
feature: DATABRICKS_UC_ADLS
phase: explore
profile: dev
status: done
approaches:
  - id: A1
    summary: "Pipeline determinístico: bundle de artefatos → collectors/extractors → facts → access graph (Graphfy) → governance.diagnose → regras SFA-* → findings → failure_layer → specialist plan → receipt"
    tradeoffs:
      - reusa `azure/governance` existente em vez de duplicar lógica de camadas
      - cenários de laboratório rodam offline via fixtures, sem contêiner
  - id: A2
    summary: Estender apenas `governance/diagnose.py`
    tradeoffs:
      - não cobre artefatos→facts→grafo→regras→recibo; o prompt exige o pipeline inteiro
  - id: A3
    summary: Fluxo LLM-primeiro com especialistas
    tradeoffs:
      - viola o princípio "LLM reasoning não é a primeira camada"
chosen: A1
---

# Explore — DATABRICKS_UC_ADLS

## Estado atual (audit)

- `azure/governance/{model,layers,diagnose}.py` avaliam Entra, UC binding, UC privileges, UC storage credential, network, RBAC e ADLS ACL sobre um `Scenario` (dict), produzem conflicts SFA-GOV-001..005, facts e findings, e são determinísticos e testados.
- `collectors/databricks.py` ingere export offline (jobs/clusters/catalogs) e tem caminho live read-only via `databricks-sdk` preguiçoso.
- `collectors/base.py` impõe redact→assert_clean→facts; `collectors/auth.py` tem auth lazy por método.
- `facts/pyspark_ast.py` extrai read/write/sql/streaming — mas não reconhece URIs `abfss://`, nomes UC de 3 partes, `dbutils` nem operações Delta.
- `rules/` tem motor `judge()` com `requires_facts`/`runtime_scope`/`blocked_on` e catálogo `pyspark.yaml` — áreas SFA-UC/ADLS/ID/NET/DBR/DELTA não existem.
- `agentic/recovery.py` já tem `FailureClass`; `agentic/memory.py` tem `environment_fingerprint`; `agentic/trust.py` tem taint.

## O que falta

Extractors de artefatos UC/RBAC/ACL/network, fatos de job/cluster (runtime, access mode, photon), scan de código para abfss/UC/dbutils/Delta, catálogo de regras de acesso, pipeline de diagnóstico end-to-end com `failure_layer` e recibo, superfícies CLI/MCP, e os 10 cenários determinísticos de laboratório com caminho de evidência.
