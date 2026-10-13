---
sdd: 1
feature: POST_MIGRATION_VALIDATION
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/POST_MIGRATION_VALIDATION/explore.md
  sha256: "2659fac70884f1d659db10e3976135ce87bc9dbb2d9f6be10d8b2c1de06c810d"
hypothesis:
  claim: "Validacao compara source/target em dimensoes (functional/data/schema/dq/performance/security/lineage/cost/orchestration); row count sozinho nunca basta; regression de performance nunca vira win"
  prediction: "mesmo row count com metrica divergente -> FAIL; perf regression -> REVIEW/FAIL mesmo com dados corretos; identidade errada no target -> security fail"
  experiment: pytest tests/test_migration_validate.py
acceptance:
- id: AC1
  statement: "dimensoes avaliadas independentemente; row-count equal + metrica divergente = FAIL"
  verified_by:
    kind: test
    ref: tests/test_migration_validate.py::test_rowcount_equal_metric_differs_fails
- id: AC2
  statement: "data match + perf regression grande = functional pass + performance review/fail"
  verified_by:
    kind: test
    ref: tests/test_migration_validate.py::test_perf_regression_never_win
- id: AC3
  statement: "identidade de seguranca errada no target -> security validation failure"
  verified_by:
    kind: test
    ref: tests/test_migration_validate.py::test_wrong_target_identity_fails
- id: AC4
  statement: "resultado nunca auto-promove; acceptance exige evidence bundle"
  verified_by:
    kind: test
    ref: tests/test_migration_validate.py::test_no_auto_promotion
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- execucao de queries de validacao; benchmark real
unknowns: []
change_kinds:
- rule
---

# Define — POST_MIGRATION_VALIDATION

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
