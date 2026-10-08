---
sdd: 1
feature: AGENT_EVAL_SUITE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_EVAL_SUITE/explore.md
  sha256: 1ea0acd8fd91f51a8522cf148d9536dd3586974529044004d3cb1373e2bc281e
hypothesis:
  claim: Cada specialist tem eval de rota executavel (positive+negative) e cada role
    aponta o teste que a cobre; evals nao resolviveis reprovam
  prediction: fleet sai de 40 unevaluated para ready onde os dims passam; casos negativos
    usam dominios disjuntos (no_match, nao below_cap)
  experiment: pytest tests/test_agent_eval_cases.py
acceptance:
- id: AC1
  statement: todo specialist tem evals/agents/<id>.yaml com >=1 route_positive e >=1
    route_negative
  verified_by:
    kind: test
    ref: tests/test_agent_eval_cases.py::test_agent_eval_cases_execute
- id: AC2
  statement: 'casos executam contra explain_route real: selected no positive, no_match
    no negative'
  verified_by:
    kind: test
    ref: tests/test_agent_eval_cases.py::test_agent_eval_cases_execute
- id: AC3
  statement: _eval_coverage resolve cada entrada contra a arvore (arquivo inexistente
    reprova)
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_eval_refs_must_exist
- id: AC4
  statement: todo manifest declara evals resolviveis — fleet honestamente avaliada
  verified_by:
    kind: test
    ref: tests/test_agentic_inventory.py::test_eval_refs_resolve_for_all_agents
success:
- id: SC1
  metric: agents list sem unevaluated com evals vazios; evals declaram artefatos reais
  source: sparkforge-azure agents list
out_of_scope:
- execucao por LLM dos evals
- model router
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — AGENT_EVAL_SUITE
