---
sdd: 1
feature: AGENT_INVENTORY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_INVENTORY/design.md
  sha256: 549eeda6b7c6b9ebacd96d85eaf456d1736663598c6c9b746fc9f41f187d3dce
tasks:
- id: T1
  files: &id001
  - sparkforge_azure/agentic/inventory.py
  - sparkforge_azure/cli/cmd_agents.py
  - sparkforge_azure/cli/main.py
  - sparkforge_azure/doctor.py
  - tests/test_agentic_inventory.py
  covers:
  - AC1
  test:
    path: tests/test_agentic_inventory.py
    name: test_every_agent_has_closed_status
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agentic_inventory.py
    name: test_inventory_is_deterministic
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agentic_inventory.py
    name: test_cli_list_and_inspect_cover_taxonomy
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agentic_inventory.py
    name: test_missing_artifacts_never_ready
- id: T5
  files: *id001
  covers:
  - AC5
  test:
    path: tests/test_agentic_inventory.py
    name: test_doctor_agentic_fleet
---

# Plan — AGENT_INVENTORY
