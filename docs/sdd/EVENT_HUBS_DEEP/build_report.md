---
sdd: 1
feature: EVENT_HUBS_DEEP
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/EVENT_HUBS_DEEP/plan.md
  sha256: "2674a896d0abc0f8a1d8731258c1dcb5be6d1faeae6f98d0e8439c9f85853f42"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-red-c4 && python -m pytest tests/test_stream_extractors.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_stream_extractors.py -q", exit: 0}
claims:
  - text: "bundle de streaming vira facts eh.*/consumer.*/offset.* deterministicamente com provenance"
    evidence_ref: "tests/test_stream_extractors.py::test_eventhubs_artifacts_become_facts"
  - text: "role_assignments e evidencia RBAC, nao segredo — role/auth_mode sobrevivem ao boundary"
    evidence_ref: "tests/test_stream_extractors.py::test_role_assignments_keep_semantics_not_redacted"
  - text: "posicoes por particao viram facts offset.position"
    evidence_ref: "tests/test_stream_extractors.py::test_partition_positions_modeled"
  - text: "metricas sao series temporais points[], nunca escalar"
    evidence_ref: "tests/test_stream_extractors.py::test_metrics_timeseries_not_point"
  - text: "SAS/connection strings nunca chegam a facts"
    evidence_ref: "tests/test_stream_extractors.py::test_sas_never_in_facts"
  - text: "throttled_requests>0 emite fact eh.throttle com total medido"
    evidence_ref: "tests/test_stream_extractors.py::test_throttle_signal_becomes_fact"
---

# Build Report — EVENT_HUBS_DEEP

Red em worktree `.tmp-red-c4` @ `86b1910` (pre-Streaming/RTI): testes copiados para o worktree falham com ModuleNotFoundError (exit 2); green em `feat/cycle4-streaming`.
