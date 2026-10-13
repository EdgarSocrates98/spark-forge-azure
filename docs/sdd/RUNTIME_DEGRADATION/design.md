---
sdd: 1
feature: RUNTIME_DEGRADATION
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/RUNTIME_DEGRADATION/define.md
  sha256: b3c8edd886c1a71adbd1f46e7919a47deaf6992ddd2f938a7c0bf52a07cf9895
files:
- path: sparkforge_azure/agentic/runtimes/fallback.py
  action: create
  reason: fallback_chain + execute_with_fallback + retry transiente
- path: tests/test_runtime_degradation.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: 'ordem §77: preferred -> playbook -> generic; transiente
    (timeout/rate-limit) retenta 1x; permanente degrada'
  rejected:
  - retry loop com backoff (§84 proibe)
  - fallback silencioso (§79 proibe)
  rollback: remover fallback.py + teste
covers:
- part: runtime_degradation
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — RUNTIME_DEGRADATION
