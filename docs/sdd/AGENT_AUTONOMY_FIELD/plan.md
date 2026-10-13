---
sdd: 1
feature: AGENT_AUTONOMY_FIELD
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_AUTONOMY_FIELD/design.md
  sha256: bc89d193d13a0d7aac1f9dd0a5025e7a51adf371c2354df77ea596bbf3e3885e
tasks:
- id: T1
  files:
  - tests/test_agent_autonomy.py
  covers:
  - AC1
  - AC2
  - AC3
  test:
    path: tests/test_agent_autonomy.py
    name: test_fleet_cap_l2
- id: T2
  files:
  - sparkforge_azure/agentmanifest/model.py
  - agents/
  - .claude/agents/custom/
  - .agents/agents/
  - agents/CAPABILITY.json
  covers:
  - AC1
  - AC3
  test:
    path: tests/test_agent_autonomy.py
    name: test_autonomy_declared_and_valid
---

# Plan — AGENT_AUTONOMY_FIELD
