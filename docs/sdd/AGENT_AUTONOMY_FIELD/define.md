---
sdd: 1
feature: AGENT_AUTONOMY_FIELD
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_AUTONOMY_FIELD/explore.md
  sha256: 7b17eb8630ef2f11dade9a3aebd42255974362e9ab5c41a6df7db985bc37d3f8
hypothesis:
  claim: 'autonomy vira REQUIRED no manifest v2: roles deterministicas L0, specialists/reviewers/subagents
    L1, coordinator+referee L2; nada >L2 na frota'
  prediction: validator recusa nivel fora do vocab; teste trava o cap de frota
  experiment: pytest tests/test_agent_autonomy.py
acceptance:
- id: AC1
  statement: todo manifest declara autonomy em L0..L5; valor fora do vocab reprova
    no validator
  verified_by:
    kind: test
    ref: tests/test_agent_autonomy.py::test_autonomy_declared_and_valid
- id: AC2
  statement: 'fleet cap: nenhum agent acima de L2 (default BOUNDED §153)'
  verified_by:
    kind: test
    ref: tests/test_agent_autonomy.py::test_fleet_cap_l2
- id: AC3
  statement: 'perfis de autonomy.py consistentes: nivel declarado resolve para AutonomyProfile
    real'
  verified_by:
    kind: test
    ref: tests/test_agent_autonomy.py::test_declared_level_resolves_profile
success:
- id: SC1
  metric: fleet 40/40 ready com autonomy declarado; cap L2 travado
  source: pytest tests/test_agent_dod.py tests/test_agent_autonomy.py
out_of_scope:
- runtime enforcement por nivel
- model router
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — AGENT_AUTONOMY_FIELD
