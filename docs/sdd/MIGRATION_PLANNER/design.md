---
sdd: 1
feature: MIGRATION_PLANNER
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_PLANNER/define.md
  sha256: "c6bacc4734ccd1ea070a2bc5b335be1e86e798ed26421054b67e55d32ba91a7e"
files:
- path: sparkforge_azure/migration/planner.py
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: migration_planner, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — MIGRATION_PLANNER
