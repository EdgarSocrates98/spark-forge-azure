---
sdd: 1
feature: AGENT_LABS_SECURITY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_LABS_SECURITY/define.md
  sha256: 27d2b615d79eb3fefef493dec770d2d84b24d1c654ac47af33b2e6638f3969a9
files:
- path: evals/agents/
  action: create
  reason: cycle 6
- path: tests/fixtures/agentic/
  action: create
  reason: cycle 6
- path: tests/test_agentic_labs.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_security_lab.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: 'A2 — labs sao suites com expect: deterministico, offline'
  rejected:
  - Labs como scripts soltos em scripts/
  - evals/agents/ + fixtures + oraculo expect como os outros labs
  rollback: reverter o commit da feature
covers:
- part: agent_labs_security
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
  - AC5
  - AC6
---

# Design — AGENT_LABS_SECURITY
