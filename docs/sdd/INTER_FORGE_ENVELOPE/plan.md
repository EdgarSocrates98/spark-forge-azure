---
sdd: 1
feature: INTER_FORGE_ENVELOPE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/INTER_FORGE_ENVELOPE/design.md
  sha256: 7017b4d71a113c5955ac783cfd732379e84e9ad64501be3605ba5219c6eb5e04
tasks:
- id: T1
  files: [tests/test_upstream_facts.py]
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_upstream_facts.py
    name: test_emitted_doc_round_trips_through_intake
- id: T2
  files: [sparkforge_azure/adapters/upstream.py]
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_upstream_facts.py
    name: test_aws_schema_envelope_is_accepted
---

# Plan — INTER_FORGE_ENVELOPE

T1 contrato (3 testes novos); T2 implementacao no mesmo arquivo do intake —
um modulo so para o envelope comum.
