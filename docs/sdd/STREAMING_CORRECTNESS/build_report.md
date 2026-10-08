---
sdd: 1
feature: STREAMING_CORRECTNESS
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_CORRECTNESS/plan.md
  sha256: "c90943163c1bf07e36bf4eb98a355ecf906529e5a242b7d163c8db7e0ad8aeb3"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-red-c4 && python -m pytest tests/test_stream_correctness.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_stream_correctness.py -q", exit: 0}
claims:
  - text: "classificacao de entrega e sempre uma de DELIVERY_ORDER"
    evidence_ref: "tests/test_stream_correctness.py::test_delivery_classification"
  - text: "additive nullable != breaking type change"
    evidence_ref: "tests/test_stream_correctness.py::test_schema_breaking_vs_additive"
  - text: "sem evidencia completa, nunca se afirma ausencia de perda — unresolved"
    evidence_ref: "tests/test_stream_correctness.py::test_no_data_loss_needs_full_evidence"
  - text: "payload hostil e DATA_ONLY, nao dirige verdict"
    evidence_ref: "tests/test_stream_correctness.py::test_payload_data_only"
---

# Build Report — STREAMING_CORRECTNESS

Red em worktree `.tmp-red-c4` @ `86b1910` (pre-Streaming/RTI): testes copiados para o worktree falham com ModuleNotFoundError (exit 2); green em `feat/cycle4-streaming`.
