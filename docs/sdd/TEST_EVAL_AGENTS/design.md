---
sdd: 1
feature: TEST_EVAL_AGENTS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/TEST_EVAL_AGENTS/define.md
  sha256: c6a80da190793e69f3bdc9c74390aee130857c04ced1c7c53c176063495f01a4
files:
- path: agents/test-engineer.md
  action: create
  reason: cycle 6
- path: agents/evaluation-specialist.md
  action: create
  reason: cycle 6
- path: sparkforge_azure/agentmanifest/model.py
  action: create
  reason: cycle 6
- path: sparkforge_azure/agentic/evalplane.py
  action: create
  reason: cycle 6
- path: tests/test_agentic_test_eval.py
  action: create
  reason: cycle 6
decisions:
- id: D1
  choice: 'A2 — test/eval e plano transversal: roles com spawn por trigger, nao routing de dominio'
  rejected:
  - Dois specialists dominio-especifico
  - Dois roles novos no plano test/eval, fora do hot path do usuario
  rollback: reverter o commit da feature
covers:
- part: test_eval_agents
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — TEST_EVAL_AGENTS
