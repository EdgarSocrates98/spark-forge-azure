---
sdd: 1
feature: ONELAKE_SECURITY_SHORTCUTS
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/ONELAKE_SECURITY_SHORTCUTS/define.md
  sha256: "d553ae8431c91cd40f533930b5cd08460f7c34ce19506ee5b29e4a98f4b78e01"
files:
- path: sparkforge_azure/fabric/security.py
  action: create
  reason: control/data plane diagnosis
- path: sparkforge_azure/fabric/shortcuts.py
  action: create
  reason: shortcut chain + effective identity
- path: rules/catalog/fabric.yaml
  action: modify
  reason: SF-FAB-SEC/SF-FAB-SC regras
- path: knowledge/azure/fabric/
  action: modify
  reason: onelake-security/shortcuts docs sourced
decisions:
- id: D1
  choice: 'grant-only: ausência de grant = denied por omissão, nunca ''deny rule'' inventada'
  rejected:
  - modelar deny roles — docs dizem que não existem
  rollback: "avaliar data plane junto do workspace; perde a separacao de camadas"
- id: D2
  choice: effective_identity fact separado de caller fact — nunca merge
  rejected:
  - single identity field — perde confused-deputy
  rollback: "colapsar caller/effective em identidade unica; reintroduz confused deputy"
- id: D3
  choice: workspace_identity como fact kind próprio ligado a workspace + conexões
  rejected:
  - tratar como user genérico
  rollback: "tratar shortcut ausente como deny; remove a distincao unresolved vs denied"
covers:
  - {part: onelake-security, acceptance: [AC1, AC2]}
  - {part: shortcuts+delegation, acceptance: [AC3, AC4, AC5]}
---

# Design — ONELAKE_SECURITY_SHORTCUTS

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
