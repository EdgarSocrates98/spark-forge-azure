---
sdd: 1
feature: FABRIC_CORE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CORE/design.md
  sha256: "79b2e9390a4fd1c1c385a94bfa3f76958ade802b7a34a77d5b2e7d07a29536ea"
tasks:
- id: T1
  files:
  - sparkforge_azure/fabric/model.py
  - sparkforge_azure/fabric/extract.py
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_fabric_extractors.py
    name: test_fabric_artifacts_become_facts
- id: T2
  files:
  - sparkforge_azure/fabric/pipeline.py
  - rules/catalog/fabric.yaml
  covers:
  - AC3
  - AC4
  test:
    path: tests/test_fabric_pipeline.py
    name: test_pipeline_end_to_end_offline
- id: T3
  files:
  - sparkforge_azure/cli/cmd_diagnose.py
  - sparkforge_azure/mcp/
  covers:
  - AC5
  test:
    path: tests/test_fabric_cli.py
    name: test_diagnose_fabric_cli_json_contract
---

# Plan — FABRIC_CORE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
