---
sdd: 1
feature: TEST_EVAL_AGENTS
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Dois specialists dominio-especifico
  tradeoffs:
  - sao transversais — plane, nao dominio
- id: A2
  summary: Dois roles novos no plano test/eval, fora do hot path do usuario
  tradeoffs:
  - spec §98/§190
  - trigger por change/release
chosen: 'A2 — test/eval e plano transversal: roles com spawn por trigger, nao routing de dominio'
---

# Explore — TEST_EVAL_AGENTS

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
