---
sdd: 1
feature: FABRIC_CORE
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Reusar azure/pipeline.py parametrizando domínio
  tradeoffs:
  - menos código
  - força semântica Databricks dentro do Fabric — viola FABRIC-NATIVE
- id: A2
  summary: Novo módulo fabric/ espelhando o padrão azure/ com casefile compartilhado
  tradeoffs:
  - semânticas próprias SaaS preservadas
  - código paralelo — mitigado reutilizando casefile/rules/ledger/graph existentes
- id: A3
  summary: Extrair GenericCloudPipeline agora
  tradeoffs:
  - 'prematuro — 60% similarity não justifica (prompt #223)'
chosen: A2 — sparkforge_azure/fabric/ com pipeline próprio; casefile/suite/rules/ledger/graphfy reutilizados
---

# Explore — FABRIC_CORE

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
