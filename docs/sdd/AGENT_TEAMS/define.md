---
sdd: 1
feature: AGENT_TEAMS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_TEAMS/explore.md
  sha256: 6f62bc2adb48e39ca753461f70659e15ed833c98a2ec4d08663c0519641ab783
hypothesis:
  claim: Cada vertical tem agent-teams/<vertical>.yaml com eligible agents; o audit garante que membership
    nao amplia privilegio (tools/context/budget ⊆ manifest proprio)
  prediction: team elegivel != spawn; audit rejeita membro que amplia privilegio
  experiment: pytest tests/test_agentic_teams.py
acceptance:
- id: AC1
  statement: 'os 4 team files validam: eligible ⊆ taxonomia, nenhum membro ampliado'
  verified_by:
    kind: test
    ref: tests/test_agentic_teams.py::test_team_files_validate
- id: AC2
  statement: 'audit detecta ampliacao: membro declarando tool/context que o manifest nao tem'
  verified_by:
    kind: test
    ref: tests/test_agentic_teams.py::test_team_audit_detects_privilege_enlargement
- id: AC3
  statement: 'composicao dinamica: team lista elegiveis; spawn depende de spawn gate, nao do arquivo'
  verified_by:
    kind: test
    ref: tests/test_agentic_teams.py::test_eligible_is_not_spawned
- id: AC4
  statement: reviewer/critic/referee/test-eval plane nunca entram como eligible de team de dominio
  verified_by:
    kind: test
    ref: tests/test_agentic_teams.py::test_control_and_eval_planes_not_in_domain_teams
success:
- id: SC1
  metric: feature verde offline com ACs cobertos
  source: pytest tests/test_agentic_teams.py
out_of_scope:
- o que nao esta na secao do prompt
unknowns: []
change_kinds:
- agent_or_skill
---

# Define — AGENT_TEAMS

Artefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.
