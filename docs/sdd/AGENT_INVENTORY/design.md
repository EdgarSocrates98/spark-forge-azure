---
sdd: 1
feature: AGENT_INVENTORY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_INVENTORY/define.md
  sha256: 2bcf2683cb544f2860fe119c626860e0d5396d898f5bad3237cf2c479374c88e
files:
- path: sparkforge_azure/agentic/inventory.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/cli/cmd_agents.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/cli/main.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/doctor.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_inventory.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: 'A2 — inventario e produto: funcao pura que todo consumidor chama'
  rejected:
  - Status por heuristica espalhada em cada consumidor
  - Modulo agentic/inventory.py com taxonomia de status fechada
  rollback: reverter o commit da feature
covers:
- part: agent_inventory
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
  - AC5
---

# Design — AGENT_INVENTORY
