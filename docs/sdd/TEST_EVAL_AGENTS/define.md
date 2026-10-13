---
sdd: 1
feature: TEST_EVAL_AGENTS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/TEST_EVAL_AGENTS/explore.md
  sha256: 42ee551f5bc3a779516cba21c6ab79bdb463d2fa52f087ec05e9596468b8476e
hypothesis:
  claim: test-engineer e evaluation-specialist existem como roles completos (manifest v2 + role plan +
    budget + evals) com tool policies distintas do resto do sistema
  prediction: test-engineer recebe artifact/code/finding/receipt; evaluation-specialist recebe eval_result/metric/receipt;
    nenhum escreve
  experiment: pytest tests/test_agentic_test_eval.py
acceptance:
- id: AC1
  statement: test-engineer e evaluation-specialist validam contra schema v2
  verified_by:
    kind: test
    ref: tests/test_agentic_test_eval.py::test_new_roles_validate_v2
- id: AC2
  statement: tool policy do test-engineer permite run tests/inspect coverage, nega cloud mutation
  verified_by:
    kind: test
    ref: tests/test_agentic_test_eval.py::test_test_engineer_tool_policy
- id: AC3
  statement: evaluation-specialist consome eval_result/metric/claim/finding — nunca artifact cru
  verified_by:
    kind: test
    ref: tests/test_agentic_test_eval.py::test_eval_specialist_context_policy
- id: AC4
  statement: spawn por trigger (change/review/release) via spawn.conditions — nunca por routing de dominio
  verified_by:
    kind: test
    ref: tests/test_agentic_test_eval.py::test_spawn_by_trigger_not_domain
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agentic_test_eval.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
---

# Define — TEST_EVAL_AGENTS

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
