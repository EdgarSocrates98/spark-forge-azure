---
sdd: 1
feature: FABRIC_CAPACITY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CAPACITY/design.md
  sha256: "aaeab5c4c39e083d58a40c1ac1349ea0d33296c19fb17a15a2a7db3c3929e319"
tasks:
- id: T1
  files:
  - sparkforge_azure/fabric/capacity.py
  - rules/catalog/fabric.yaml
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_fabric_capacity.py
    name: test_overload_is_not_throttling
- id: T2
  files:
  - sparkforge_azure/fabric/capacity.py
  covers:
  - AC5
  test:
    path: tests/test_fabric_capacity.py
    name: test_spark_vs_capacity_attribution
---

# Plan — FABRIC_CAPACITY

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
