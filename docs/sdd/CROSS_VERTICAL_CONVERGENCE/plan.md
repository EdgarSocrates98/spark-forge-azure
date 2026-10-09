---
sdd: 1
feature: CROSS_VERTICAL_CONVERGENCE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/CROSS_VERTICAL_CONVERGENCE/design.md
  sha256: "f23c40e2e355c79e77d55579dea671e4e86b2485aae4625b0af489a179c1a157"
tasks:
- id: T1
  files:
  - sparkforge_azure/azure/fingerprint.py
  - sparkforge_azure/azure/pipeline.py
  covers: [AC1]
  test:
    path: tests/test_cross_vertical_convergence.py
    name: test_environment_fingerprint_deterministico
- id: T2
  files:
  - sparkforge_azure/migration/pipeline.py
  covers: [AC2]
  test:
    path: tests/test_cross_vertical_convergence.py
    name: test_lab_all_cells_pass
- id: T3
  files:
  - evals/convergence/suite.yaml
  - evals/convergence/cases/access_s01.yaml
  - evals/convergence/cases/fabric_f05.yaml
  - evals/convergence/cases/stream_s08.yaml
  - evals/convergence/cases/migration_m02.yaml
  - evals/convergence/runner.py
  covers: [AC3]
  test:
    path: tests/test_cross_vertical_convergence.py
    name: test_lab_all_cells_pass
- id: T4
  files:
  - tests/test_cross_vertical_convergence.py
  covers: [AC4]
  test:
    path: tests/test_cross_vertical_convergence.py
    name: test_contaminacao_de_memoria
---

# Plan — CROSS_VERTICAL_CONVERGENCE

Implementacao ja medida: runner reporta 20/20 celulas verdes;
fingerprint de databricks deterministico com workspace_id +
subscription_id + storage_account derivados; evidence_paths de
migration resolve SF-MIG-002 -> f_b970a1 -> estate.json.
