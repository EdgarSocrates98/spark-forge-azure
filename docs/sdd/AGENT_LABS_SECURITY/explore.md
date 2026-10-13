---
sdd: 1
feature: AGENT_LABS_SECURITY
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Labs como scripts soltos em scripts/
  tradeoffs:
  - sem oraculo
  - sem determinismo
- id: A2
  summary: evals/agents/ + fixtures + oraculo expect como os outros labs
  tradeoffs:
  - mesmo contrato do Forge Lab
chosen: 'A2 — labs sao suites com expect: deterministico, offline'
---

# Explore — AGENT_LABS_SECURITY

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
