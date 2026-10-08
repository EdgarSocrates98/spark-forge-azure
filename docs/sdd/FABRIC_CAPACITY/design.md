---
sdd: 1
feature: FABRIC_CAPACITY
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_CAPACITY/define.md
  sha256: "57f98c19a7d793fa31e3509947b03a261f17677e12a0893edd047945f2fdb8fd"
files:
- path: sparkforge_azure/fabric/capacity.py
  action: create
  reason: capacity states + evidence-only throttling
- path: rules/catalog/fabric.yaml
  action: modify
  reason: SF-FAB-CAP regras
decisions:
- id: D1
  choice: estados explícitos documentados; unresolved como default sem evidence
  rejected:
  - score de saúde — inventa precisão
- id: D2
  choice: 429 errorCodes (RequestBlocked vs CapacityLimitExceeded) como facts de rejection evidence
  rejected:
  - 429 genérico — confunde rate limit com capacity
covers:
- AC1
- AC2
- AC3
- AC4
- AC5
---

# Design — FABRIC_CAPACITY

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
