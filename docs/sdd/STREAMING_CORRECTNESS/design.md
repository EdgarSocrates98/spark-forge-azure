---
sdd: 1
feature: STREAMING_CORRECTNESS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_CORRECTNESS/define.md
  sha256: "6707eb5ebcaa3d82cf6805acc592bdcc34734e9c1e4f749d2714ab92d63b3c50"
files:
- path: sparkforge_azure/stream/correctness.py
  action: create
  reason: "delivery semantics + schema compat + data-loss candidates"
- path: rules/catalog/stream.yaml
  action: create
  reason: "catalogo SF-STR-*"
decisions:
- id: D1
  choice: "classificador deterministico sobre facts; LLM nunca decide semantics"
  rejected:
  - "classificacao livre pelo agente"
  rollback: "reverter para texto livre; perde auditabilidade"
- id: D2
  choice: "SF-STR-* catalogo unico para streaming Databricks-side; RTI recebe SF-RTI-* separado"
  rejected:
  - "um catalogo gigante unico"
  rollback: "fundir os dois; areas de regra se misturam"
covers:
  - {part: correctness+catalog, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — STREAMING_CORRECTNESS
