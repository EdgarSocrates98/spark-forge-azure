---
sdd: 1
feature: AGENT_TEAMS
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_TEAMS/design.md
  sha256: 32cb57afab5988c4b379fe2539a6c81e1e92a7732f1ca8849949f901bbe11a19
tasks:
- id: T1
  files: &id001
  - agent-teams/databricks.yaml
  - agent-teams/fabric.yaml
  - agent-teams/streaming.yaml
  - agent-teams/migration.yaml
  - sparkforge_azure/agentic/teams.py
  - tests/test_agentic_teams.py
  covers:
  - AC1
  test:
    path: tests/test_agentic_teams.py
    name: test_team_files_validate
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agentic_teams.py
    name: test_team_audit_detects_privilege_enlargement
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agentic_teams.py
    name: test_eligible_is_not_spawned
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agentic_teams.py
    name: test_control_and_eval_planes_not_in_domain_teams
---

# Plan — AGENT_TEAMS
