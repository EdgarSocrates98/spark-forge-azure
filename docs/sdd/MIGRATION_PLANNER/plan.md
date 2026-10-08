---
sdd: 1
feature: MIGRATION_PLANNER
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_PLANNER/design.md
  sha256: "108284affefeecbc1293408313c60376f6c64c1c6a7b194623fb2e753fe2589b"
tasks:
- id: T1
  files:
  - sparkforge_azure/migration/planner.py
  covers:
  - AC1
  test:
    path: tests/test_migration_planner.py
    name: test_waves_topological_order
- id: T2
  files:
  - sparkforge_azure/migration/planner.py
  covers:
  - AC2
  test:
    path: tests/test_migration_planner.py
    name: test_cycle_is_review_not_fake_order
- id: T3
  files:
  - sparkforge_azure/migration/planner.py
  covers:
  - AC3
  test:
    path: tests/test_migration_planner.py
    name: test_wave_has_rollback
- id: T4
  files:
  - sparkforge_azure/migration/planner.py
  covers:
  - AC4
  test:
    path: tests/test_migration_planner.py
    name: test_shared_upstream_blocks_wave
---

# Plan — MIGRATION_PLANNER
