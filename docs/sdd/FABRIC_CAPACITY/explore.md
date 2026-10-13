---
sdd: 1
feature: FABRIC_CAPACITY
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Inferir throttling de utilization>100%
  tradeoffs:
  - semanticamente errado (#77) — smoothing torna >100% normal
- id: A2
  summary: 'Estados explícitos: healthy/overloaded_without_observed_throttling/throttled/rejection/unresolved; throttling só com evidence (evento, erro CapacityLimitExceeded, métrica de delay/reject)'
  tradeoffs:
  - honesto
  - precisa de artifacts de métricas — cobertos por export offline + fixtures
chosen: A2 — capacidade é entidade de 1ª classe; evidence-based, nunca threshold mágico
---

# Explore — FABRIC_CAPACITY

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
