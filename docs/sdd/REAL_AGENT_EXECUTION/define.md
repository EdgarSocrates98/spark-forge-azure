---
sdd: 1
feature: REAL_AGENT_EXECUTION
phase: define
profile: dev
status: done
hypothesis:
  claim: 'engine canonico §24: run_case liga plan_pipeline -> spawn gate ->
    adapter -> schema validation -> receipt; output por role com schema
    fechado §96-103; output invalido = contract_violation (§103), nunca
    coercao silenciosa (§104)'
  prediction: run_case com runtime generic executa roles L0 inline de
    verdade e marca roles probabilisticas unresolved com razao nomeada
  experiment: pytest tests/test_agent_execution.py
acceptance:
- id: AC1
  statement: 'schemas por role: specialist/reviewer/verifier/referee/
    test_engineer/evaluation_specialist com campos §97-102; validacao
    fail-closed devolve contract_violation'
  verified_by:
    kind: test
    ref: tests/test_agent_execution.py::test_role_schemas_validate
- id: AC2
  statement: 'run_case executa o fluxo canonico: spawn gate decide, adapter
    executa, resultado tem receipt com execution_mode + fingerprint'
  verified_by:
    kind: test
    ref: tests/test_agent_execution.py::test_run_case_canonical_flow
- id: AC3
  statement: 'role probabilistica em runtime sem host: status unresolved +
    razao nomeada, nunca sucesso vazio nem erro de processo'
  verified_by:
    kind: test
    ref: tests/test_agent_execution.py::test_probabilistic_role_unresolved
- id: AC4
  statement: 'output do host e DATA_ONLY: freeform vira
    PROVISIONAL_AGENT_OUTPUT; nada vira verified sem verificacao (§31-32)'
  verified_by:
    kind: test
    ref: tests/test_agent_execution.py::test_host_output_is_provisional
success:
- id: SC1
  metric: run_case produz AgentExecutionReceipt completo em runtime generic;
    schema violations detectadas
  source: pytest tests/test_agent_execution.py
out_of_scope:
- execucao LLM real de specialist (host nao disponivel)
- paralelismo real (§208 nested desligado)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — REAL_AGENT_EXECUTION
