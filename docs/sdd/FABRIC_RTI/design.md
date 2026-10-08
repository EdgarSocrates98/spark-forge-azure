---
sdd: 1
feature: FABRIC_RTI
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_RTI/define.md
  sha256: "f645198c002c920c03146bf284d29ce824dacf7e1ace61ad01c9c6346663c0b1"
files:
- path: sparkforge_azure/stream/rti.py
  action: create
  reason: "cadeia RTI: eventstream->eventhouse->activator"
- path: rules/catalog/rti.yaml
  action: create
  reason: "catalogo SF-RTI-*"
decisions:
- id: D1
  choice: "RTI dentro de stream/ como subcadeia — reusa casefile/facts/graph, sem pacote paralelo"
  rejected:
  - "pacote fabric_rti separado"
  rollback: "extrair pacote separado; duplica pipeline"
- id: D2
  choice: "schema-aware Eventstreams marcado preview quando docs indicarem; nunca GA por omissao"
  rejected:
  - "tratar como GA"
  rollback: "remover flag; risco de claim falso"
covers:
  - {part: rti chain+catalog, acceptance: [AC1, AC2, AC3, AC4]}
---

# Design — FABRIC_RTI
