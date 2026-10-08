---
sdd: 1
feature: AGENT_LABS_SECURITY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_LABS_SECURITY/explore.md
  sha256: a797ec5f60c8422465e48733e4b95b415f0cb2d72585f2755e284097947880f6
hypothesis:
  claim: 'Os labs §171-183 existem como casos deterministicos: routing esperado, negative routing, overlap
    minimo, conflito->referee, critic em risco, budget stop, security deny, taint preservado, memory poison
    rejeitado'
  prediction: routing lab cobre os 6 casos canonicos; security lab recusa tool fora da policy; taint nunca
    lava
  experiment: pytest tests/test_agentic_labs.py
acceptance:
- id: AC1
  statement: 'routing lab: cada caso canonico roteia para o specialist esperado e so ele'
  verified_by:
    kind: test
    ref: tests/test_agentic_labs.py::test_routing_lab_expected_specialists
- id: AC2
  statement: 'negative routing: caso sem dominio nao spawna specialist'
  verified_by:
    kind: test
    ref: tests/test_agentic_labs.py::test_negative_routing_lab
- id: AC3
  statement: 'security lab: tool fora da policy nega; confused deputy nega; impersonation detecta'
  verified_by:
    kind: test
    ref: tests/test_agentic_security_lab.py::test_security_lab_denies
- id: AC4
  statement: 'taint lab: output malicioso de specialist chega ao receiver com taint preservado'
  verified_by:
    kind: test
    ref: tests/test_agentic_security_lab.py::test_handoff_taint_lab
- id: AC5
  statement: 'budget lab: budget insuficiente -> stop graceful com reason nomeada'
  verified_by:
    kind: test
    ref: tests/test_agentic_labs.py::test_budget_lab_graceful_stop
- id: AC6
  statement: 'memory lab: memoria envenenada e rejeitada/quarentenada, nunca autoridade'
  verified_by:
    kind: test
    ref: tests/test_agentic_security_lab.py::test_memory_poison_rejected
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agentic_labs.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
- fixture_corpus
---

# Define — AGENT_LABS_SECURITY

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
