---
sdd: 1
feature: STREAMING_CORRECTNESS
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Estender vertical access/fabric com flags de dominio streaming
  tradeoffs:
  - menos codigo
  - mistura semantica temporal/stateful em cadeia batch — viola SEMANTICS>MARKETING
- id: A2
  summary: Novo modulo stream/ espelhando fabric/ reutilizando casefile/rules/ledger/graphfy/tokensave
  tradeoffs:
  - semanticas proprias preservadas (progress windows, checkpoint, RTI chain)
  - codigo paralelo — mitigado reusando kernels existentes
- id: A3
  summary: Extrair StreamingKernel generico agora
  tradeoffs:
  - 'prematuro — um vertical novo nao justifica kernel (prompt #329)'
chosen: A2 — sparkforge_azure/stream/ com pipeline proprio; nucleo reutilizado
---

# Explore — STREAMING_CORRECTNESS

Artefatos do Cycle 4; ver prompt_evo_cycle4.md.
