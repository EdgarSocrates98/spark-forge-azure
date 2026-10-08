---
sdd: 1
feature: DATA_ONELAKE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/DATA_ONELAKE/design.md
  sha256: "a97d3c200837520e5641091477984054889c46d8b1e78dda86b93251ef194ff2"
tasks:
- id: T1
  files:
  - sparkforge_azure/migration/data.py
  covers:
  - AC1
  test:
    path: tests/test_migration_data.py
    name: test_strategy_closed_set_with_evidence
- id: T2
  files:
  - sparkforge_azure/migration/data.py
  covers:
  - AC2
  test:
    path: tests/test_migration_data.py
    name: test_delta_shortcut_candidate_not_forced
- id: T3
  files:
  - sparkforge_azure/migration/data.py
  covers:
  - AC3
  test:
    path: tests/test_migration_data.py
    name: test_retirement_prefers_copy
- id: T4
  files:
  - sparkforge_azure/migration/data.py
  covers:
  - AC4
  test:
    path: tests/test_migration_data.py
    name: test_hms_managed_external_split
---

# Plan — DATA_ONELAKE
