---
sdd: 1
feature: MIGRATION_COMPATIBILITY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_COMPATIBILITY/explore.md
  sha256: "46c58adac25d4db068e5f627af2382377cdf6379afb2d3bdb602b8ac76e1a829"
hypothesis:
  claim: "Um compatibility engine deterministico por dimensao (activity/connector/auth/IR/network/parameter/trigger/expression/notebook/runtime/library/config/path/catalog/git/deployment) produz status compativel/change/refactor/unsupported/preview/unknown sem magic score"
  prediction: "cada dimensao emite status+evidence; score agrega sem esconder blockers; unknown nunca vira compatible"
  experiment: pytest tests/test_migration_compat.py
acceptance:
- id: AC1
  statement: "toda dimensao avaliada retorna status do vocabulario fechado + evidence"
  verified_by:
    kind: test
    ref: tests/test_migration_compat.py::test_dimensions_closed_vocabulary
- id: AC2
  statement: "unsupported/explicit > review; ausencia de evidencia e unknown, nao compatible"
  verified_by:
    kind: test
    ref: tests/test_migration_compat.py::test_absence_is_unknown_not_compatible
- id: AC3
  statement: "score, se existir, e auxiliar e nunca esconde blockers/unknowns/refactors"
  verified_by:
    kind: test
    ref: tests/test_migration_compat.py::test_score_never_hides_blockers
- id: AC4
  statement: "conflito oficial-vs-Forge vira REVIEW com provenance, nunca override silencioso"
  verified_by:
    kind: test
    ref: tests/test_migration_compat.py::test_official_conflict_is_review
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- catalogo completo de conectores ADF; parity matrix oficial viva
unknowns: []
change_kinds:
- rule
- rule_area
---

# Define — MIGRATION_COMPATIBILITY

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
