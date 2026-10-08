---
sdd: 1
feature: AGENT_CONTRACT_V2
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Schema novo paralelo (agents/v2/)
  tradeoffs:
  - dois schemas pra manter
  - deriva garantida
- id: A2
  summary: Evoluir schema no lugar, chaves novas obrigatorias
  tradeoffs:
  - fonte unica
  - migracao atomica
chosen: A2 — fonte canonica unica; v2 endurece contrato sem fork de diretorio
---

# Explore — AGENT_CONTRACT_V2

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
