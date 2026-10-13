---
sdd: 1
feature: MIGRATION_INVENTORY
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_INVENTORY/explore.md
  sha256: "18c64857063372faefdd3f376784d618bc9b0b1c2b38ff60e1a33e378ac55fef"
hypothesis:
  claim: "Um estate bundle (ADF factory + Synapse workspace + Fabric target) vira facts adf.*/synapse.*/fabric.* com dependencias tipadas; ausencia de assessment nunca vira READY"
  prediction: "bundles produzem facts de asset+dependency com provenance; estate summary conta ready/review/blocked/unresolved; assessment ausente -> unresolved"
  experiment: pytest tests/test_migration_inventory.py
acceptance:
- id: AC1
  statement: "asset types do catalogo (#14) viram facts com canonical id (ARM/GUID), nunca display name"
  verified_by:
    kind: test
    ref: tests/test_migration_inventory.py::test_assets_have_canonical_ids
- id: AC2
  statement: "dependency edges (contains/uses/reads/writes/invokes/depends_on/runs_on) sao facts tipados"
  verified_by:
    kind: test
    ref: tests/test_migration_inventory.py::test_dependency_facts_are_typed
- id: AC3
  statement: "estate summary conta asset/dependency/unsupported/review/ready/unknown; ausencia nao e READY"
  verified_by:
    kind: test
    ref: tests/test_migration_inventory.py::test_absence_is_unresolved_not_ready
- id: AC4
  statement: "secrets de linked service (conn string/SAS/key) nunca entram em facts"
  verified_by:
    kind: test
    ref: tests/test_migration_inventory.py::test_linked_service_secrets_redacted
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- collectors live ADF/Synapse/Fabric; assessment oficial MS parsing completo
unknowns: []
change_kinds:
- extractor
- fixture_corpus
---

# Define — MIGRATION_INVENTORY

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
