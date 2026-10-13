---
sdd: 1
feature: SKILL_EVAL_KIND_COVERAGE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_EVAL_KIND_COVERAGE/explore.md
  sha256: d7fa976e9d9f71c6682feab65e6641fcadf4e7bd70af933085aa83ec5a15aa74
hypothesis:
  claim: Toda skill tem ao menos um caso negative (rota para dominio adjacente) e
    um boundary (borda do escopo), sem mudar o contrato v1
  prediction: as 8 nao-verticais recebem 2 casos cada; teste na arvore real garante
    a cobertura
  experiment: pytest tests/test_skills.py -k eval_kinds
acceptance:
- id: AC1
  statement: toda skill tem >=1 caso kind=negative e >=1 kind=boundary
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_every_skill_has_negative_and_boundary_evals
- id: AC2
  statement: 'casos novos passam nas regras existentes: must_include grounded, expected_tools
    declaradas, sem overlap'
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_every_skill_has_statically_checkable_evals
success:
- id: SC1
  metric: 22/22 skills com negative+boundary; strict validator verde
  source: pytest tests/test_skills.py && scripts/check_skills_agents.py
out_of_scope:
- mudar VERTICAL_SKILLS ou o contrato v1
- reescrever casos existentes
unknowns: []
change_kinds:
- agent_or_skill
---

# Define — SKILL_EVAL_KIND_COVERAGE
