---
sdd: 1
feature: FABRIC_CAPACITY
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CAPACITY/plan.md
  sha256: "bf0055db7b2b55717d7979e74bda52834143fca6d227dcc33d8e11b30bb85ce9"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_capacity.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_capacity.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_capacity.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_capacity.py::test_spark_vs_capacity_attribution -q", exit: 0}
claims:
  - text: "capacity vira fact com estado/utilizacao observados"
    evidence_ref: "tests/test_fabric_capacity.py::test_capacity_facts"
  - text: "overload alto NAO e throttling — sem evidencia de throttle o veredito nao e capacity"
    evidence_ref: "tests/test_fabric_capacity.py::test_overload_is_not_throttling"
  - text: "throttling so e reportado com evidencia explicita"
    evidence_ref: "tests/test_fabric_capacity.py::test_throttled_with_evidence"
  - text: "sem metricas de capacity a camada fica unresolved"
    evidence_ref: "tests/test_fabric_capacity.py::test_no_metrics_unresolved"
  - text: "Spark lento com capacity saudavel atribui a camada spark, nao capacity"
    evidence_ref: "tests/test_fabric_capacity.py::test_spark_vs_capacity_attribution"
---

# Build Report — FABRIC_CAPACITY

Red em worktree base `068b922` (pre-Fabric), green em `feat/cycle3-fabric-deep`. Detalhes no frontmatter.
