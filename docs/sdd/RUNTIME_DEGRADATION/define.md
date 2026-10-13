---
sdd: 1
feature: RUNTIME_DEGRADATION
phase: define
profile: dev
status: done
hypothesis:
  claim: 'fallback explicito §77: host real -> sequential -> playbook ->
    deterministic core; execute_with_fallback registra degraded_reason;
    retry so em falha transiente e nunca em loop (§83-84)'
  prediction: runtime indisponivel degrada para playbook com razao nomeada;
    timeout vira UNRESOLVED; falha permanente nao retenta
  experiment: pytest tests/test_runtime_degradation.py
acceptance:
- id: AC1
  statement: 'fallback_chain(preferred) segue a ordem §77 ate o floor
    deterministico; cada degrada produz degraded_reason'
  verified_by:
    kind: test
    ref: tests/test_runtime_degradation.py::test_fallback_order
- id: AC2
  statement: 'execute_with_fallback em host sem binario degrada para
    playbook/inline e reporta execution_mode + degraded_reason (§78-80)'
  verified_by:
    kind: test
    ref: tests/test_runtime_degradation.py::test_degradation_is_explicit
- id: AC3
  statement: 'retry: so falha transiente retenta, 1x, e nunca loop
    (§83-84,206); permanente nao retenta'
  verified_by:
    kind: test
    ref: tests/test_runtime_degradation.py::test_retry_only_transient_once
- id: AC4
  statement: 'partial team: falha de um estagio nao derruba o case e o
    receipt mostra degradacao (§86,§200-203)'
  verified_by:
    kind: test
    ref: tests/test_runtime_degradation.py::test_partial_failure_degrades
success:
- id: SC1
  metric: degradacao sempre explicita; zero silent fallback; timeout ->
    unresolved
  source: pytest tests/test_runtime_degradation.py
out_of_scope:
- execucao de host real
- retry com backoff (fora — so transiente unico)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — RUNTIME_DEGRADATION
