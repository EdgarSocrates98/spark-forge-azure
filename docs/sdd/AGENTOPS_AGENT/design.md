---
sdd: 1
feature: AGENTOPS_AGENT
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENTOPS_AGENT/define.md
  sha256: db230b846c54db0fab4f011297680b9660467ed16b5e04bd42a71736f4b07b19
files:
- path: sparkforge_azure/agentic/spans.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/observability/agentops.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_spans.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: A2 — §56 exige campos de agent; §156 exige receipt de execucao
  rejected:
  - Estender spans existentes com campos agent
  - AgentSpan proprio + AgentExecutionReceipt agregando considered/spawned/skipped
  rollback: reverter o commit da feature
covers:
- part: agentops_agent
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — AGENTOPS_AGENT
