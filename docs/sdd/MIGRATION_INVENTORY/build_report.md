---
sdd: 1
feature: MIGRATION_INVENTORY
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_INVENTORY/plan.md
  sha256: "ce10efeec8d0073ef7d4a826be2ef8cdc1ee924823f6f62ae34376824bdec64a"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_inventory.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_inventory.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_inventory.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_inventory.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_inventory.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_inventory.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_inventory.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_inventory.py -q", exit: 0}
claims:
  - text: "asset types do catalogo (#14) viram facts com canonical id (ARM/GUID), nunca display name"
    evidence_ref: "tests/test_migration_inventory.py::test_assets_have_canonical_ids"
  - text: "dependency edges (contains/uses/reads/writes/invokes/depends_on/runs_on) sao facts tipados"
    evidence_ref: "tests/test_migration_inventory.py::test_dependency_facts_are_typed"
  - text: "estate summary conta asset/dependency/unsupported/review/ready/unknown; ausencia nao e READY"
    evidence_ref: "tests/test_migration_inventory.py::test_absence_is_unresolved_not_ready"
  - text: "secrets de linked service (conn string/SAS/key) nunca entram em facts"
    evidence_ref: "tests/test_migration_inventory.py::test_linked_service_secrets_redacted"
---

# Build Report — MIGRATION_INVENTORY

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
