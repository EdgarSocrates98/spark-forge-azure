---
sdd: 1
feature: AGENT_VALUE_EVAL
phase: define
profile: dev
status: done
hypothesis:
  claim: 'harness A/B §50-75: 4 cases x configs A-D mesmo input; EvalResult
    formato §75; value_vector §57 (nunca escalar); classify_necessity §59-60;
    custo/token unresolved sem host (§55)'
  prediction: reports deterministicos por config; forbidden finding ->
    HARMFUL; sem ganho de info -> NEUTRAL/USEFUL; nunca score unico
  experiment: pytest tests/test_agent_value_eval.py
acceptance:
- id: AC1
  statement: '4 cases em evals/agent_runtime/cases + expected + configs
    A-D; evaluate_case produz result por config com campos §75'
  verified_by:
    kind: test
    ref: tests/test_agent_value_eval.py::test_eval_result_format
- id: AC2
  statement: 'mesmo input entre configs (§52) — cases identicos, so o
    conjunto de estagios muda'
  verified_by:
    kind: test
    ref: tests/test_agent_value_eval.py::test_same_input_across_configs
- id: AC3
  statement: 'value_vector tem as 7 dims §57 e necessity usa vocab fechado
    {ESSENTIAL,USEFUL,NEUTRAL,HARMFUL,UNRESOLVED}'
  verified_by:
    kind: test
    ref: tests/test_agent_value_eval.py::test_value_vector_and_necessity
- id: AC4
  statement: 'sem host: tokens/cost reportam unresolved (§55); forbidden
    finding produzido -> HARMFUL'
  verified_by:
    kind: test
    ref: tests/test_agent_value_eval.py::test_honest_cost_and_harmful
success:
- id: SC1
  metric: reports em evals/agent_runtime/reports por case; frontier A-D
    por qualidade evidencial
  source: pytest tests/test_agent_value_eval.py
out_of_scope:
- custo de token real (sem host/provider)
- claims "agents improve quality" sem metrica (§193)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — AGENT_VALUE_EVAL
