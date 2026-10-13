---
sdd: 1
feature: POST_MIGRATION_VALIDATION
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/POST_MIGRATION_VALIDATION/define.md
  sha256: "2f3b33456d3876466d2c351a2f982d3f1f0dcc3984b6587b3d2b17afc17e31fa"
files:
- path: sparkforge_azure/migration/validate.py
  action: create
  reason: "vertical migration"
decisions:
- id: D1
  choice: "IDs oficiais/ARM como identidade; display name vira attr; DATA_ONLY para assessments Microsoft"
  rejected:
  - "name-based identity / override silencioso do assessment oficial"
  rollback: "reverter para chave por nome; ids sao triviais de trocar"
covers:
  - {part: post_migration_validation, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — POST_MIGRATION_VALIDATION
