---
sdd: 1
feature: MIGRATION_PLANNER
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_PLANNER/explore.md
  sha256: "f790e8a3a6a7e34176f2906db11657654d0f0e71a44df1d5ad513ab99a27400b"
hypothesis:
  claim: "O planner gera waves por ordem topologica do grafo de dependencias; ciclo de dependencia vira REVIEW, nunca ordem fabricada; cada wave carrega rollback plan e freeze window"
  prediction: "waves ordenadas por dependencia; ciclo detectado -> REVIEW; cutover define parallel-run/shadow; rollback define trigger+steps+data divergence"
  experiment: pytest tests/test_migration_planner.py
acceptance:
- id: AC1
  statement: "waves respeitam ordem topologica das dependencias de asset"
  verified_by:
    kind: test
    ref: tests/test_migration_planner.py::test_waves_topological_order
- id: AC2
  statement: "ciclo de dependencia de migracao -> REVIEW, nunca wave inventada"
  verified_by:
    kind: test
    ref: tests/test_migration_planner.py::test_cycle_is_review_not_fake_order
- id: AC3
  statement: "cada wave carrega receipt + rollback (trigger/steps/divergence) definidos"
  verified_by:
    kind: test
    ref: tests/test_migration_planner.py::test_wave_has_rollback
- id: AC4
  statement: "asset upstream compartilhado bloqueia wave candidate"
  verified_by:
    kind: test
    ref: tests/test_migration_planner.py::test_shared_upstream_blocks_wave
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- execucao de cutover; freeze enforcement
unknowns: []
change_kinds:
- rule
---

# Define — MIGRATION_PLANNER

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
