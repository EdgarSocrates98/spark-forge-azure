---
sdd: 1
feature: AGENT_MIRRORS
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_MIRRORS/design.md
  sha256: ddb66f0c027c7f6cd99bdb18bf6cf4496407cef2b07ec1fbf07eb283139755d0
tasks:
- id: T1
  files:
  - tests/test_agent_mirrors.py
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_agent_mirrors.py
    name: test_real_tree_agent_mirrors_in_sync
- id: T2
  files:
  - sparkforge_azure/agentmanifest/mirrors.py
  - scripts/sync_agent_mirrors.py
  - scripts/check_skills_agents.py
  covers:
  - AC1
  - AC2
  - AC4
  test:
    path: tests/test_agent_mirrors.py
    name: test_agent_mirror_drift_and_sync
---

# Plan — AGENT_MIRRORS
