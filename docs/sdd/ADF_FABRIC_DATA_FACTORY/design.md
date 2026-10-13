---
sdd: 1
feature: ADF_FABRIC_DATA_FACTORY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/ADF_FABRIC_DATA_FACTORY/define.md
  sha256: "f6045178af9e05e2e527513f9d05932228102618cfd37fd5969810463f892132"
files:
- path: sparkforge_azure/migration/pipelines.py
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: adf_fabric_data_factory, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — ADF_FABRIC_DATA_FACTORY
