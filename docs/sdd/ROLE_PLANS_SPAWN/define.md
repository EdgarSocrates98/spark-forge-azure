---
sdd: 1
feature: ROLE_PLANS_SPAWN
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/ROLE_PLANS_SPAWN/explore.md
  sha256: e14dc8b65fee8637aeed14b6ba06355efcb5710f3119f47054c123825468936a
hypothesis:
  claim: Todo agent tem RoleContextPlan derivado do proprio manifest; spawn decision devolve SPAWN|SKIP|DEFER
    com reason e information gain estruturado; route explica por que cada agent entrou ou ficou de fora
  prediction: spawn sem sinal de dominio = SKIP; incerteza no dominio do specialist = SPAWN; route expõe
    razao por candidato
  experiment: pytest tests/test_agentic_role_plans.py
acceptance:
- id: AC1
  statement: todo agent da taxonomia resolve um RoleContextPlan valido (derivado do manifest)
  verified_by:
    kind: test
    ref: tests/test_agentic_role_plans.py::test_every_agent_has_role_plan
- id: AC2
  statement: spawn decision retorna SPAWN|SKIP|DEFER + reason estruturada
  verified_by:
    kind: test
    ref: tests/test_agentic_spawn.py::test_spawn_decision_closed_vocabulary
- id: AC3
  statement: sem dominio/unresolved no dominio do agent -> SKIP; high uncertainty no dominio -> SPAWN
  verified_by:
    kind: test
    ref: tests/test_agentic_spawn.py::test_spawn_gate_semantics
- id: AC4
  statement: 'route explica por candidato: matched terms, decision, reason; deterministico'
  verified_by:
    kind: test
    ref: tests/test_agentic_spawn.py::test_route_explainability
- id: AC5
  statement: 'handoff nunca escala privilegio: receiver plan filtra, taint preservado'
  verified_by:
    kind: test
    ref: tests/test_agentic_role_plans.py::test_no_privilege_escalation_on_handoff
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agentic_role_plans.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
---

# Define — ROLE_PLANS_SPAWN

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
