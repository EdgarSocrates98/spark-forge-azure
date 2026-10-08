---
sdd: 1
feature: FABRIC_CAPACITY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CAPACITY/design.md
  sha256: "e1ae1ae9dc3adc265196a50b98c5a2a2d822b698152f760c25093d304656fd79"
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
