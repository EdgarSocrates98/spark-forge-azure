---
sdd: 1
feature: DATA_ONELAKE
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/DATA_ONELAKE/explore.md
  sha256: "33feadccdfdff044a6b7ac7b7fc731a5c9fb6cae89d87956cd69e8caf8a8e77f"
hypothesis:
  claim: "Cada categoria de dados (delta tables/files/managed/external/lake database) recebe estrategia retain/shortcut/copy/hybrid com evidence — shortcut-first quando elegivel, nunca mandatorio"
  prediction: "Delta no ADLS -> shortcut candidate; source retirement -> copy; HMS/lake database metadata -> assessment dedicado; zero-copy != zero-cost/risk"
  experiment: pytest tests/test_migration_data.py
acceptance:
- id: AC1
  statement: "recommendation e uma de retain/shortcut/copy/hybrid com dims de decisao (formato/retirement/egress/latency)"
  verified_by:
    kind: test
    ref: tests/test_migration_data.py::test_strategy_closed_set_with_evidence
- id: AC2
  statement: "Delta elegivel vira shortcut candidate mas nunca recomendacao forcada"
  verified_by:
    kind: test
    ref: tests/test_migration_data.py::test_delta_shortcut_candidate_not_forced
- id: AC3
  statement: "retirement da fonte pende para copy quando evidencia suporta"
  verified_by:
    kind: test
    ref: tests/test_migration_data.py::test_retirement_prefers_copy
- id: AC4
  statement: "managed vs external tables + HMS sao avaliados separadamente"
  verified_by:
    kind: test
    ref: tests/test_migration_data.py::test_hms_managed_external_split
success:
- id: SC1
  metric: pipeline migration verde offline; readiness correto por caso; claims novos com prova
  source: pytest tests/test_migration_*.py
out_of_scope:
- execucao de copia real; mirroring; CDC
unknowns: []
change_kinds:
- rule
---

# Define — DATA_ONELAKE

Artefato do Cycle 5 (ADF/Synapse -> Fabric migration vertical); ver prompt_evo_cycle5.md.
