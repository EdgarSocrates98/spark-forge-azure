---
sdd: 1
feature: FABRIC_RTI
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_RTI/plan.md
  sha256: "2358c7a6b10218b280e01eb252b6d89504c993a0474cb2ee5fa8802d6002a880"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-red-c4 && python -m pytest tests/test_stream_rti.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_stream_rti.py -q", exit: 0}
claims:
  - text: "eventstream.json vira facts rti.* avaliados por estagio"
    evidence_ref: "tests/test_stream_rti.py::test_eventstream_facts"
  - text: "falha de source e de destination sao camadas distintas"
    evidence_ref: "tests/test_stream_rti.py::test_destination_vs_source_layers"
  - text: "activator mapping invalido != avaliacao stale"
    evidence_ref: "tests/test_stream_rti.py::test_activator_mapping_vs_evaluation"
  - text: "acao do activator exige evidencia; ausencia nunca vira pass"
    evidence_ref: "tests/test_stream_rti.py::test_activator_action_needs_evidence"
---

# Build Report — FABRIC_RTI

Red em worktree `.tmp-red-c4` @ `86b1910` (pre-Streaming/RTI): testes copiados para o worktree falham com ModuleNotFoundError (exit 2); green em `feat/cycle4-streaming`.
