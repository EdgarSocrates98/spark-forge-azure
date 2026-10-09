---
sdd: 1
feature: AGENT_AUTONOMY_FIELD
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_AUTONOMY_FIELD/define.md
  sha256: dd7ad970d934e7cce2444e63e4a1d49cc82dd9bdfe0dcf05011c1ef7a1ecd57b
files:
- path: sparkforge_azure/agentmanifest/model.py
  action: modify
  reason: autonomy REQUIRED + vocab fechado
- path: tests/test_agent_autonomy.py
  action: create
  reason: contrato do campo
- path: agents/
  action: modify
  reason: 'autonomy: L0/L1/L2 nos 40 manifests'
- path: .claude/agents/custom/
  action: modify
  reason: mirrors regen
- path: .agents/agents/
  action: modify
  reason: mirrors regen
- path: agents/CAPABILITY.json
  action: modify
  reason: regen com autonomy
decisions:
- id: D1
  choice: autonomy REQUIRED com vocab {L0..L5}; coordinator/referee L2, deterministicas
    L0, resto L1; cap L2 por teste
  rejected:
  - campo opcional (§153 pede default travado)
  - string livre (vocab aberto)
  rollback: reverter o commit da feature
covers:
- part: agent_autonomy_field
  acceptance:
  - AC1
  - AC2
  - AC3
---

# Design — AGENT_AUTONOMY_FIELD
