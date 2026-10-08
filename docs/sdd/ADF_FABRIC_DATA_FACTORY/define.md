---
sdd: 1
feature: ADF_FABRIC_DATA_FACTORY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/ADF_FABRIC_DATA_FACTORY/explore.md
  sha256: "920c30dd025a33d6b83d65929c70a82e4ac42c69fc49a1907d1f367e020d269d"
hypothesis:
  claim: "Pipelines ADF/Synapse sao avaliadas por atividade/conector/linked-service/IR/parametro/trigger/expressao com readiness READY/REVIEW/BLOCKED/MANUAL/DEFERRED/UNRESOLVED e recomendacao tipada"
  prediction: "linked services viram candidatos a Fabric Connection; global params viram Variable Library; SHIR vira review de rede/IR; trigger/activity incompativel bloqueia"
  experiment: pytest tests/test_migration_pipelines.py
acceptance:
- id: AC1
  statement: "activity/connector incompativeis produzem blocker com evidence exata"
  verified_by:
    kind: test
    ref: tests/test_migration_pipelines.py::test_unsupported_activity_blocks
- id: AC2
  statement: "global parameters viram variable_library candidate; linked services viram connection candidates com auth assessment"
  verified_by:
    kind: test
    ref: tests/test_migration_pipelines.py::test_global_params_and_linked_services_map
- id: AC3
  statement: "SHIR/IR dependente exige review de rede; nunca auto-mapped"
  verified_by:
    kind: test
    ref: tests/test_migration_pipelines.py::test_shir_is_manual_review
- id: AC4
  statement: "pipelines que dividem linked service com auth incompativel nao consolidam connection"
  verified_by:
    kind: test
    ref: tests/test_migration_pipelines.py::test_no_blind_connection_consolidation
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- auto-rewrite de pipeline JSON; todas as activities ADF
unknowns: []
change_kinds:
- rule
- extractor
---

# Define — ADF_FABRIC_DATA_FACTORY

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
