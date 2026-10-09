---
sdd: 1
feature: AGENTIC_ARCHITECTURE_FREEZE
phase: define
profile: dev
status: done
hypothesis:
  claim: 'freeze gate §179-181: avalia as 6 condicoes contra evidencia real;
    security lab §112-120 verde; resultado honesto — candidate bloqueado em
    host_proven, nao congelado sem prova (§9/§176)'
  prediction: FREEZE_STATUS = candidate/deferred com razao nomeada; nenhuma
    condicao marcada verde sem prova
  experiment: pytest tests/test_agent_runtime_security.py
    tests/test_architecture_freeze.py
acceptance:
- id: AC1
  statement: 'security lab: output hostil fica DATA_ONLY/provisional; tool
    escalation nega; subagent nunca spawna; verified facts nunca vem de
    adapter (§113-120)'
  verified_by:
    kind: test
    ref: tests/test_agent_runtime_security.py::test_malicious_agent_output_stays_data_only
- id: AC2
  statement: 'freeze evaluator devolve as 6 condicoes §180 com status
    evidenciado; host_proven ausente -> FREEZE_STATUS=candidate'
  verified_by:
    kind: test
    ref: tests/test_architecture_freeze.py::test_freeze_conditions_evidence
- id: AC3
  statement: '5 docs §189 + RUNTIME_EXECUTION_OUTCOME.md com campos §191
    todos presentes e honestos (NOT_OBSERVED onde nao medido)'
  verified_by:
    kind: test
    ref: tests/test_architecture_freeze.py::test_outcome_brief_fields
success:
- id: SC1
  metric: freeze decidido por evidencia; outcome brief completo
  source: pytest tests/test_architecture_freeze.py
out_of_scope:
- freeze efetivo (depende de host proof)
- segundo host adapter (§232 so se justificado por medida)
unknowns: []
change_kinds:
- agent_or_skill
- knowledge_doc
---

# Define — AGENTIC_ARCHITECTURE_FREEZE
