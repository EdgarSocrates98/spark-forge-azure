---
sdd: 1
feature: FABRIC_GRAPH_TOKENSAVE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_GRAPH_TOKENSAVE/define.md
  sha256: "0c167b5d398061490c3c9a57512adfb33ca001effe4a7db2b0ead06dff103ed8"
files:
- path: sparkforge_azure/graph/fabric.py
  action: create
  reason: fabric graph builder + queries
- path: evals/token_efficient/fabric_case/
  action: create
  reason: corpus benchmark Fabric
- path: knowledge/packs.yaml
  action: modify
  reason: packs fabric-*
- path: sparkforge_azure/knowledgebase/vertical.py
  action: modify
  reason: scoping por failure_layer fabric_*
decisions:
- id: D1
  choice: graph/fabric.py dentro do Graphfy existente
  rejected:
  - segundo graph — proibido
  rollback: "criar grafo fabric fora do Graphfy; duplica o motor"
- id: D2
  choice: failure layers fabric_* namespaced — não colidem com Cycle 2
  rejected:
  - reusar SF-ACC — domínio diferente
  rollback: "reusar layers SF-ACC sem namespace; colide com Cycle 2"
covers:
  - {part: graph, acceptance: [AC1, AC2, AC3, AC4]}
  - {part: tokensave, acceptance: [AC5]}
  - {part: knowledge, acceptance: [AC6]}
  - {part: agentops, acceptance: [AC7]}
---

# Design — FABRIC_GRAPH_TOKENSAVE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
