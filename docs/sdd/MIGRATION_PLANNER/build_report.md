---
sdd: 1
feature: MIGRATION_PLANNER
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_PLANNER/plan.md
  sha256: "33179df6229337cc80f5cc7cb77d7432a53e2265c94a0c205cf62d7a48b83aca"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_planner.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_planner.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_planner.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_planner.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_planner.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_planner.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_planner.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_planner.py -q", exit: 0}
claims:
  - text: "waves respeitam ordem topologica das dependencias de asset"
    evidence_ref: "tests/test_migration_planner.py::test_waves_topological_order"
  - text: "ciclo de dependencia de migracao -> REVIEW, nunca wave inventada"
    evidence_ref: "tests/test_migration_planner.py::test_cycle_is_review_not_fake_order"
  - text: "cada wave carrega receipt + rollback (trigger/steps/divergence) definidos"
    evidence_ref: "tests/test_migration_planner.py::test_wave_has_rollback"
  - text: "asset upstream compartilhado bloqueia wave candidate"
    evidence_ref: "tests/test_migration_planner.py::test_shared_upstream_blocks_wave"
---

# Build Report — MIGRATION_PLANNER

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
