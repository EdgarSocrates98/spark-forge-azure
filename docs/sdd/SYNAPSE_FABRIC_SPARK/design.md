---
sdd: 1
feature: SYNAPSE_FABRIC_SPARK
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/SYNAPSE_FABRIC_SPARK/define.md
  sha256: "8d761841fa0ee0ffda05b7fbc7b4072b8772059cf19eca4b4f26c59965dcadce"
files:
- path: sparkforge_azure/migration/spark.py
  action: create
  reason: "vertical migration"
- path: sparkforge_azure/migration/codeintel_mig.py
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: synapse_fabric_spark, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — SYNAPSE_FABRIC_SPARK
