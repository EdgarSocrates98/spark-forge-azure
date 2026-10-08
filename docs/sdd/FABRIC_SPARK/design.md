---
sdd: 1
feature: FABRIC_SPARK
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_SPARK/define.md
  sha256: "f8f75394a66d4732628b6ef5f6e6e1ba1bdfd7aadf774555422f09b3fd436a2e"
files:
- path: sparkforge_azure/fabric/spark.py
  action: create
  reason: runtime/env/SJD diagnosis
- path: sparkforge_azure/fabric/runtime_matrix.yaml
  action: create
  reason: matrix versionada+sourced
- path: rules/catalog/fabric.yaml
  action: modify
  reason: SF-FAB-SPARK regras
- path: sparkforge_azure/facts/notebook_scan.py
  action: modify
  reason: padrões OneLake/mssparkutils
decisions:
- id: D1
  choice: runtime matrix em YAML versionado com source+verified_at por linha
  rejected:
  - hardcode em código — perde freshness gate
  rollback: "mover a matrix para codigo; perde freshness por fonte"
- id: D2
  choice: default lakehouse = aresta notebook/job→lakehouse no grafo
  rejected:
  - attr solto — perde impact queries
  rollback: "voltar a default_lakehouse como attr; perde impact queries no grafo"
covers:
  - {part: runtime+lakehouse, acceptance: [AC1, AC2, AC3]}
  - {part: jobdef+scanner, acceptance: [AC4, AC5]}
---

# Design — FABRIC_SPARK

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
