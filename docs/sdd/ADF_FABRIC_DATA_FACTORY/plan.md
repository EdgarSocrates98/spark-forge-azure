---
sdd: 1
feature: ADF_FABRIC_DATA_FACTORY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/ADF_FABRIC_DATA_FACTORY/design.md
  sha256: "2ac87f32bcffeefa0744536c7ec1287a38bb8a1d6a629f0e7abbae631256665c"
tasks:
- id: T1
  files:
  - sparkforge_azure/migration/pipelines.py
  covers:
  - AC1
  test:
    path: tests/test_migration_pipelines.py
    name: test_unsupported_activity_blocks
- id: T2
  files:
  - sparkforge_azure/migration/pipelines.py
  covers:
  - AC2
  test:
    path: tests/test_migration_pipelines.py
    name: test_global_params_and_linked_services_map
- id: T3
  files:
  - sparkforge_azure/migration/pipelines.py
  covers:
  - AC3
  test:
    path: tests/test_migration_pipelines.py
    name: test_shir_is_manual_review
- id: T4
  files:
  - sparkforge_azure/migration/pipelines.py
  covers:
  - AC4
  test:
    path: tests/test_migration_pipelines.py
    name: test_no_blind_connection_consolidation
---

# Plan — ADF_FABRIC_DATA_FACTORY
