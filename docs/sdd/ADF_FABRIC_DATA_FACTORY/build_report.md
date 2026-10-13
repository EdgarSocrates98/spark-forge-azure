---
sdd: 1
feature: ADF_FABRIC_DATA_FACTORY
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/ADF_FABRIC_DATA_FACTORY/plan.md
  sha256: "aebfe882a7e6fdc04c606141fd11a894c8e997d4bd192f5d8797045ab0c4fd36"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_pipelines.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_pipelines.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_pipelines.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_pipelines.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_pipelines.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_pipelines.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_pipelines.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_pipelines.py -q", exit: 0}
claims:
  - text: "activity/connector incompativeis produzem blocker com evidence exata"
    evidence_ref: "tests/test_migration_pipelines.py::test_unsupported_activity_blocks"
  - text: "global parameters viram variable_library candidate; linked services viram connection candidates com auth assessment"
    evidence_ref: "tests/test_migration_pipelines.py::test_global_params_and_linked_services_map"
  - text: "SHIR/IR dependente exige review de rede; nunca auto-mapped"
    evidence_ref: "tests/test_migration_pipelines.py::test_shir_is_manual_review"
  - text: "pipelines que dividem linked service com auth incompativel nao consolidam connection"
    evidence_ref: "tests/test_migration_pipelines.py::test_no_blind_connection_consolidation"
---

# Build Report — ADF_FABRIC_DATA_FACTORY

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
