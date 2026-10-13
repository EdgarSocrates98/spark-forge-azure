---
sdd: 1
feature: REAL_HANDOFF_EXECUTION
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/REAL_HANDOFF_EXECUTION/define.md
  sha256: 65d9156d2db82420b212db411b273ca0795b87f05d18aa86504e155aed0ede05
files:
- path: sparkforge_azure/agentic/execution.py
  action: modify
  reason: handoff emission + resume + stage fingerprint
- path: tests/test_handoff_execution.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: resume compara stage_fingerprint (agent+role plan+context+runtime);
    divergente ou ausente re-executa; identico devolve record marcado skipped
  rejected:
  - cache por agent_id puro (manifest/contexto mudariam em silencio)
  - rerun sempre (§47 proibe)
  rollback: reverter commit
covers:
- part: real_handoff_execution
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — REAL_HANDOFF_EXECUTION
