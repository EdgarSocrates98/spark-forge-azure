---
sdd: 1
feature: FABRIC_SPARK
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_SPARK/plan.md
  sha256: "d2fdaf64569656d3e77d4a2ff941a0e2ffe2a2b3a2b61b8fdf7d62c9fd5e4e50"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_spark.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_spark.py::test_missing_default_lakehouse tests/test_fabric_spark.py::test_wrong_default_lakehouse -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_spark.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_spark.py::test_retry_idempotency_finding -q", exit: 0}
claims:
  - text: "runtime nunca e adivinhado: environment ausente -> unresolved, mismatch -> finding SF-FAB"
    evidence_ref: "tests/test_fabric_spark.py::test_runtime_never_guessed"
  - text: "SparkJobDefinition sem default lakehouse e diagnostico proprio"
    evidence_ref: "tests/test_fabric_spark.py::test_missing_default_lakehouse"
  - text: "default lakehouse errado difere de ausente"
    evidence_ref: "tests/test_fabric_spark.py::test_wrong_default_lakehouse"
  - text: "retry policy sem evidencia de idempotencia gera finding"
    evidence_ref: "tests/test_fabric_spark.py::test_retry_idempotency_finding"
  - text: "notebook Fabric reutiliza o scanner PySpark compartilhado + catalogo SF-PY"
    evidence_ref: "tests/test_fabric_spark.py::test_notebook_scan_onelake_paths"
---

# Build Report — FABRIC_SPARK

Red em worktree base `068b922` (pre-Fabric), green em `feat/cycle3-fabric-deep`. Detalhes no frontmatter.
