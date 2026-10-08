---
sdd: 1
feature: MIGRATION_COMPATIBILITY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_COMPATIBILITY/design.md
  sha256: "7de9d3e983af8342e1d5bed64f0f9507017841fd137c8fa1e5b736b04df069af"
tasks:
- id: T1
  files:
  - sparkforge_azure/migration/compat.py
  - rules/catalog/migration.yaml
  covers:
  - AC1
  test:
    path: tests/test_migration_compat.py
    name: test_dimensions_closed_vocabulary
- id: T2
  files:
  - sparkforge_azure/migration/compat.py
  - rules/catalog/migration.yaml
  covers:
  - AC2
  test:
    path: tests/test_migration_compat.py
    name: test_absence_is_unknown_not_compatible
- id: T3
  files:
  - sparkforge_azure/migration/compat.py
  - rules/catalog/migration.yaml
  covers:
  - AC3
  test:
    path: tests/test_migration_compat.py
    name: test_score_never_hides_blockers
- id: T4
  files:
  - sparkforge_azure/migration/compat.py
  - rules/catalog/migration.yaml
  covers:
  - AC4
  test:
    path: tests/test_migration_compat.py
    name: test_official_conflict_is_review
---

# Plan — MIGRATION_COMPATIBILITY
