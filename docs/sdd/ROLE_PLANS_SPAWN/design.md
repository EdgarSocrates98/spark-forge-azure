---
sdd: 1
feature: ROLE_PLANS_SPAWN
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/ROLE_PLANS_SPAWN/define.md
  sha256: bd07663c47420f93421313eb6c4c86aa70db931e9c0c8e2ff10d660f3bcf83e7
files:
- path: sparkforge_azure/agentic/role_plans.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/agentic/spawn.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/cli/cmd_agents.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_role_plans.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_spawn.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: A2 — o manifest ja declara allowed/required context; o plano deriva dele
  rejected:
  - Tabela ROLE_PLANS escrita a mao para todos os agents
  - RoleContextPlan derivado do manifest (fonte unica) + overrides minimos
  rollback: reverter o commit da feature
covers:
- part: role_plans_spawn
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
  - AC5
---

# Design — ROLE_PLANS_SPAWN
