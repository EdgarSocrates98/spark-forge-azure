---
sdd: 1
feature: MIGRATION_INVENTORY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_INVENTORY/design.md
  sha256: "c0388fde9c786edbdce88cad51a7aa94901813919c69092c2c9db0f7c38a1f62"
tasks:
- id: T1
  files:
  - sparkforge_azure/migration/__init__.py
  - sparkforge_azure/migration/model.py
  - sparkforge_azure/migration/casefile.py
  - sparkforge_azure/migration/extract.py
  - sparkforge_azure/migration/inventory.py
  covers:
  - AC1
  test:
    path: tests/test_migration_inventory.py
    name: test_assets_have_canonical_ids
- id: T2
  files:
  - sparkforge_azure/migration/__init__.py
  - sparkforge_azure/migration/model.py
  - sparkforge_azure/migration/casefile.py
  - sparkforge_azure/migration/extract.py
  - sparkforge_azure/migration/inventory.py
  covers:
  - AC2
  test:
    path: tests/test_migration_inventory.py
    name: test_dependency_facts_are_typed
- id: T3
  files:
  - sparkforge_azure/migration/__init__.py
  - sparkforge_azure/migration/model.py
  - sparkforge_azure/migration/casefile.py
  - sparkforge_azure/migration/extract.py
  - sparkforge_azure/migration/inventory.py
  covers:
  - AC3
  test:
    path: tests/test_migration_inventory.py
    name: test_absence_is_unresolved_not_ready
- id: T4
  files:
  - sparkforge_azure/migration/__init__.py
  - sparkforge_azure/migration/model.py
  - sparkforge_azure/migration/casefile.py
  - sparkforge_azure/migration/extract.py
  - sparkforge_azure/migration/inventory.py
  covers:
  - AC4
  test:
    path: tests/test_migration_inventory.py
    name: test_linked_service_secrets_redacted
---

# Plan — MIGRATION_INVENTORY
