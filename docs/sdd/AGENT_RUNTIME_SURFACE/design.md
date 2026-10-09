---
sdd: 1
feature: AGENT_RUNTIME_SURFACE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_RUNTIME_SURFACE/define.md
  sha256: eb3481472ca3da7c696f15a920f5923dcaeb19d032870626d5b6e201a098ac91
files:
- path: sparkforge_azure/agentic/spans.py
  action: modify
  reason: campos §122 + spans_from_execution
- path: sparkforge_azure/cli/cmd_agents.py
  action: modify
  reason: runtimes/runtime-inspect/execute/compare
- path: sparkforge_azure/mcp/agent_tools.py
  action: modify
  reason: sfa_agents_runtimes + sfa_agents_execution_explain
- path: sparkforge_azure/doctor.py
  action: modify
  reason: check agent_runtime
- path: docs/surface.lock.json
  action: modify
  reason: +2 tools
- path: docs/reference/mcp-tools.md
  action: modify
  reason: catalogo 15->17
- path: tests/test_runtime_surface.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: execute e sempre dry-run na CLI (host execution via opt-in do
    adapter, nunca por flag de CLI)
  rejected:
  - --execute flag na CLI (§199 — execucao explicita mas nao casual)
  rollback: reverter commit + regen surface lock
covers:
- part: agent_runtime_surface
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — AGENT_RUNTIME_SURFACE
