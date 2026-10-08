---
sdd: 1
feature: FABRIC_GRAPH_TOKENSAVE
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Grafo Fabric separado
  tradeoffs:
  - proibido (#13) — graph/ existente absorve nova domain layer
- id: A2
  summary: Node kinds fabric_*/onelake_* + edges com provenance no Graphfy existente; benchmark TokenSave com corpus Fabric; knowledge packs escopados; spans fabric.*
  tradeoffs:
  - integra tudo que já existe
  - precisa de prefix discipline pra não colidir com azure_ kinds
chosen: A2 — integração total; evidence paths derivados do grafo como no Cycle 2
---

# Explore — FABRIC_GRAPH_TOKENSAVE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
