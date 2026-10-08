---
sdd: 1
feature: AGENT_INVENTORY
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Status por heuristica espalhada em cada consumidor
  tradeoffs:
  - duplicacao
  - deriva
- id: A2
  summary: Modulo agentic/inventory.py com taxonomia de status fechada
  tradeoffs:
  - fonte unica
  - testavel
chosen: 'A2 — inventario e produto: funcao pura que todo consumidor chama'
---

# Explore — AGENT_INVENTORY

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
