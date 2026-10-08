---
sdd: 1
feature: AGENT_TEAMS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_TEAMS/define.md
  sha256: 16818a6ab53c98ddacabe352505248faa9a06acc93861213b44f1e4e55ba8a2c
files:
- path: agent-teams/databricks.yaml
  action: create
  reason: cycle 6
- path: agent-teams/fabric.yaml
  action: create
  reason: cycle 6
- path: agent-teams/streaming.yaml
  action: create
  reason: cycle 6
- path: agent-teams/migration.yaml
  action: create
  reason: cycle 6
- path: sparkforge_azure/agentic/teams.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_teams.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: A2 — arquivo define elegibilidade; runtime compoe dinamicamente
  rejected:
  - Teams hardcoded em python
  - 'agent-teams/*.yaml: eligible + rules, runtime decide subconjunto'
  rollback: reverter o commit da feature
covers:
- part: agent_teams
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — AGENT_TEAMS
