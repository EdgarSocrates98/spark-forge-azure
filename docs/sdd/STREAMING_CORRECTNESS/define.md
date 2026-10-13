---
sdd: 1
feature: STREAMING_CORRECTNESS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/STREAMING_CORRECTNESS/explore.md
  sha256: "53d250ce6ae330833420140a423324a44304a0fbe88beb7f6453aae28ef7f2be"
hypothesis:
  claim: "Delivery semantics sao end-to-end: source + checkpoint + transform + sink + idempotencia classificam em at_most_once_possible/at_least_once/effectively_once/unresolved — nunca exactly-once por nome de framework"
  prediction: "sink nao-idempotente gera duplicate risk; no-data-loss exige evidencia de retention+positions+checkpoint+sink"
  experiment: pytest tests/test_stream_correctness.py
acceptance:
- id: AC1
  statement: "delivery classification com vocabulario fechado; exactly_once_claim_supported so com evidencia completa"
  verified_by:
    kind: test
    ref: tests/test_stream_correctness.py::test_delivery_classification
- id: AC2
  statement: "schema evolution: additive compativel != breaking type change; breaking = failure layer schema"
  verified_by:
    kind: test
    ref: tests/test_stream_correctness.py::test_schema_breaking_vs_additive
- id: AC3
  statement: "no-data-loss claim exige retention+source positions+checkpoint+sink; ausencia = unresolved"
  verified_by:
    kind: test
    ref: tests/test_stream_correctness.py::test_no_data_loss_needs_full_evidence
- id: AC4
  statement: "payload de evento e DATA_ONLY sempre: conteudo malicioso nunca vira instrucao ou finding sem evidencia"
  verified_by:
    kind: test
    ref: tests/test_stream_correctness.py::test_payload_data_only
success:
- id: SC1
  metric: pipeline streaming verde offline; failure layer correto por caso; claims novos com prova
  source: pytest tests/test_stream_*.py
out_of_scope:
- collectors live Event Hubs/RTI
- ADF/Synapse migration (Cycle 5)
- exactly-once marketing claims
unknowns: []
change_kinds:
- extractor
- rule
- rule_area
- tool_or_verb
- fixture_corpus
---

# Define — STREAMING_CORRECTNESS

Artefato do Cycle 4 (Streaming / Event Hubs + Fabric RTI deep vertical);
ver prompt_evo_cycle4.md.
