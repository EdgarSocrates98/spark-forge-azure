---
sdd: 1
feature: POST_MIGRATION_VALIDATION
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/POST_MIGRATION_VALIDATION/design.md
  sha256: "b676ab934f6325c80d6628ee8f5c48fee761309f7697c99f1f78bd481b89e0e8"
tasks:
- id: T1
  files:
  - sparkforge_azure/migration/validate.py
  covers:
  - AC1
  test:
    path: tests/test_migration_validate.py
    name: test_rowcount_equal_metric_differs_fails
- id: T2
  files:
  - sparkforge_azure/migration/validate.py
  covers:
  - AC2
  test:
    path: tests/test_migration_validate.py
    name: test_perf_regression_never_win
- id: T3
  files:
  - sparkforge_azure/migration/validate.py
  covers:
  - AC3
  test:
    path: tests/test_migration_validate.py
    name: test_wrong_target_identity_fails
- id: T4
  files:
  - sparkforge_azure/migration/validate.py
  covers:
  - AC4
  test:
    path: tests/test_migration_validate.py
    name: test_no_auto_promotion
---

# Plan — POST_MIGRATION_VALIDATION
