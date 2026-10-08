---
sdd: 1
feature: MIGRATION_PLANNER
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Estender vertical fabric/stream com flags de dominio migration
  tradeoffs:
  - menos codigo
  - readiness/waves/rollback sao semanticas proprias — violaria DEPTH>BREADTH
- id: A2
  summary: Novo modulo migration/ espelhando stream/ reutilizando casefile/rules/ledger/graphfy/tokensave
  tradeoffs:
  - semanticas proprias preservadas (readiness, compatibility dims, waves)
  - codigo paralelo — mitigado reusando kernels existentes
- id: A3
  summary: Extrair MigrationKernel generico agora
  tradeoffs:
  - 'prematuro — um vertical novo nao justifica kernel (sem kernel extraction, prompt #315)'
chosen: A2 — sparkforge_azure/migration/ com pipeline proprio; nucleo reutilizado
---

# Explore — MIGRATION_PLANNER


Alternativas avaliadas; modulo dedicado escolhido para preservar semanticas de migracao (readiness, blockers, waves) sem misturar com verticais de acesso/fabric/stream.
