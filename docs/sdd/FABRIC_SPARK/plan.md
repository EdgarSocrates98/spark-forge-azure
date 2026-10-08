---
sdd: 1
feature: FABRIC_SPARK
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_SPARK/design.md
  sha256: "8c40c385a8f843bee8edf53fb2e8bcc7c90f449095d04b66bc8e44a4e0ed65da"
tasks:
- id: T1
  files:
  - sparkforge_azure/fabric/runtime_matrix.yaml
  - sparkforge_azure/fabric/spark.py
  covers:
  - AC1
  - AC4
  test:
    path: tests/test_fabric_spark.py
    name: test_runtime_never_guessed
- id: T2
  files:
  - sparkforge_azure/fabric/spark.py
  covers:
  - AC2
  - AC3
  test:
    path: tests/test_fabric_spark.py
    name: test_missing_default_lakehouse
- id: T3
  files:
  - sparkforge_azure/facts/notebook_scan.py
  covers:
  - AC5
  test:
    path: tests/test_fabric_spark.py
    name: test_notebook_scan_onelake_paths
---

# Plan — FABRIC_SPARK

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
