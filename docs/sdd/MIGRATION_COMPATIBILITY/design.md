---
sdd: 1
feature: MIGRATION_COMPATIBILITY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_COMPATIBILITY/define.md
  sha256: "e496747ab639283bfda246987245558f5acbc10e4c35e31ff61fa843df137aad"
files:
- path: sparkforge_azure/migration/compat.py
  action: create
  reason: "vertical migration"
- path: rules/catalog/migration.yaml
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: migration_compatibility, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — MIGRATION_COMPATIBILITY
