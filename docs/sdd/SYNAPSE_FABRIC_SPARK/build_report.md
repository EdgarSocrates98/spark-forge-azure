---
sdd: 1
feature: SYNAPSE_FABRIC_SPARK
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/SYNAPSE_FABRIC_SPARK/plan.md
  sha256: "aa9c11d16ffb6ee4adc31fcd570965a5f11a0bd2c7c38fa519a867e460c83e70"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_spark.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_spark.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_spark.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_spark.py -q", exit: 0}
claims:
  - text: "patterns oficiais de refactor detectados por ocorrencia com evidence (mssparkutils, synapsesql, catalog API, linked-service paths)"
    evidence_ref: "tests/test_migration_spark.py::test_refactor_patterns_detected"
  - text: "spark config custom classificada (supported/change/unsupported) sem mapear compute 1:1"
    evidence_ref: "tests/test_migration_spark.py::test_spark_config_classified"
  - text: "library sem compatibilidade provada e REVIEW/UNRESOLVED, nunca unsupported inventado"
    evidence_ref: "tests/test_migration_spark.py::test_library_unknown_is_review"
  - text: "notebook dependency graph alimenta blast radius"
    evidence_ref: "tests/test_migration_spark.py::test_notebook_dependency_graph"
---

# Build Report — SYNAPSE_FABRIC_SPARK

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
