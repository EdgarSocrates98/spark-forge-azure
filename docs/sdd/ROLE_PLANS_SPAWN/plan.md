---
sdd: 1
feature: ROLE_PLANS_SPAWN
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/ROLE_PLANS_SPAWN/design.md
  sha256: 1829fb67245b1c8a5f275bcff0ac1d27155e113d3c37178c574fc4826b84e7e4
tasks:
- id: T1
  files: &id001
  - sparkforge_azure/agentic/role_plans.py
  - sparkforge_azure/agentic/spawn.py
  - sparkforge_azure/cli/cmd_agents.py
  - tests/test_agentic_role_plans.py
  - tests/test_agentic_spawn.py
  covers:
  - AC1
  test:
    path: tests/test_agentic_role_plans.py
    name: test_every_agent_has_role_plan
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agentic_spawn.py
    name: test_spawn_decision_closed_vocabulary
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agentic_spawn.py
    name: test_spawn_gate_semantics
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agentic_spawn.py
    name: test_route_explainability
- id: T5
  files: *id001
  covers:
  - AC5
  test:
    path: tests/test_agentic_role_plans.py
    name: test_no_privilege_escalation_on_handoff
---

# Plan — ROLE_PLANS_SPAWN
