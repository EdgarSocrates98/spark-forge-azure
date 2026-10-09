---
sdd: 1
feature: REAL_AGENT_EXECUTION
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/REAL_AGENT_EXECUTION/define.md
  sha256: ee2737a954477c5e1544e4696fa338d92ea119b356927cc21a27003bff2ac4ce
files:
- path: sparkforge_azure/agentic/schemas.py
  action: create
  reason: schemas de output por role + validate fail-closed
- path: sparkforge_azure/agentic/execution.py
  action: create
  reason: run_case — engine canonico + AgentExecutionReceipt
- path: tests/test_agent_execution.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: schema validation retorna contract_violation nomeado; freeform
    -> PROVISIONAL_AGENT_OUTPUT; adapter unresolved nao quebra o caso
  rejected:
  - coercao silenciosa de output ruim (§104 proibe)
  - crash do case em output invalido (§201 proibe)
  rollback: remover schemas.py/execution.py + teste
covers:
- part: real_agent_execution
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — REAL_AGENT_EXECUTION
