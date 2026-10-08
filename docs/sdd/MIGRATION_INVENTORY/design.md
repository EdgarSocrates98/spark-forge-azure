---
sdd: 1
feature: MIGRATION_INVENTORY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_INVENTORY/define.md
  sha256: "ec65e6414fd6d4d11238cbdac2dc6ada6ca93ade039c06ca66d2713f86d64f06"
files:
- path: sparkforge_azure/migration/__init__.py
  action: create
  reason: "vertical migration"
- path: sparkforge_azure/migration/model.py
  action: create
  reason: "vertical migration"
- path: sparkforge_azure/migration/casefile.py
  action: create
  reason: "vertical migration"
- path: sparkforge_azure/migration/extract.py
  action: create
  reason: "vertical migration"
- path: sparkforge_azure/migration/inventory.py
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: migration_inventory, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — MIGRATION_INVENTORY
