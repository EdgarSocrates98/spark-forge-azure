---
sdd: 1
feature: AGENT_DOD_GATE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_DOD_GATE/design.md
  sha256: 8c5c6d0211b7949f945f0362f3396a378ba117747bf3ced6afa89f72b4e8f259
tasks:
- id: T1
  files:
  - tests/test_agent_dod.py
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_agent_dod.py
    name: test_core_dod_all_agents
- id: T2
  files:
  - scripts/gen_agent_capability.py
  - agents/CAPABILITY.json
  - CONTRIBUTING.md
  covers:
  - AC3
  - AC4
  test:
    path: tests/test_agent_dod.py
    name: test_capability_manifest_in_sync
---

# Plan — AGENT_DOD_GATE
