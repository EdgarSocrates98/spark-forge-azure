---
sdd: 1
feature: AGENT_DOD_GATE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_DOD_GATE/define.md
  sha256: ae22f05b00288eede608a7e9a71ac541deef82bd1bef115764c323b41405dabd
files:
- path: tests/test_agent_dod.py
  action: create
  reason: DoD por familia
- path: scripts/gen_agent_capability.py
  action: create
  reason: gera CAPABILITY.json
- path: agents/CAPABILITY.json
  action: create
  reason: artefato gerado
- path: CONTRIBUTING.md
  action: modify
  reason: gate de novo agent
decisions:
- id: D1
  choice: capability manifest deriva do inventory() + manifests (deterministico);
    gate = checklist no CONTRIBUTING enforced pelos testes de contrato
  rejected:
  - YAML autoral (deriva)
  - gate so em texto (nao enforced)
  rollback: reverter o commit da feature
covers:
- part: agent_dod_gate
  acceptance:
  - AC1
  - AC2
  - AC3
  - AC4
---

# Design — AGENT_DOD_GATE
