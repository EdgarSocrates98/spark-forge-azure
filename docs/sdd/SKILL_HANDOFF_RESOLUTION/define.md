---
sdd: 1
feature: SKILL_HANDOFF_RESOLUTION
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_HANDOFF_RESOLUTION/explore.md
  sha256: 82412e01e2ee0072fdfd788dd0ed5e24c90b77834ee322d7fb50392280c071ca
hypothesis:
  claim: Todo alvo de `## Handoff` em SKILL.md resolve para uma skill ou um agent
    da taxonomia; alvo desconhecido e recusa nomeada
  prediction: a auditoria encontra `migration` sem resolucao em azure-synapse e iceberg;
    corrigido para migration-specialist, a arvore inteira passa
  experiment: pytest tests/test_skills.py -k handoff
acceptance:
- id: AC1
  statement: todo alvo de handoff em SKILL.md resolve para uma skill ou um agent da
    taxonomia
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_handoff_targets_resolve
- id: AC2
  statement: migration corrigido para migration-specialist nas duas skills afetadas
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_handoff_targets_resolve
- id: AC3
  statement: alvo desconhecido produz recusa nomeada do validador
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_handoff_target_unknown_refused
success:
- id: SC1
  metric: validate_skills_tree verde com check de handoff ativo
  source: pytest tests/test_skills.py
out_of_scope:
- reescrita semantica dos handoffs existentes
- novas skills
unknowns: []
change_kinds:
- agent_or_skill
---

# Define — SKILL_HANDOFF_RESOLUTION
