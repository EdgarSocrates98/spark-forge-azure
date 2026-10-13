---
sdd: 1
feature: DATA_ONELAKE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/DATA_ONELAKE/define.md
  sha256: "0bb37b972c041fbc3b294125b9805702656b82f7838f950b9b66dea684b34886"
files:
- path: sparkforge_azure/migration/data.py
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: data_onelake, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — DATA_ONELAKE
