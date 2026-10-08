---
sdd: 1
feature: ROLE_PLANS_SPAWN
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Tabela ROLE_PLANS escrita a mao para todos os agents
  tradeoffs:
  - deriva contra o manifest
- id: A2
  summary: RoleContextPlan derivado do manifest (fonte unica) + overrides minimos
  tradeoffs:
  - sem duplicata
  - manifest e contrato
chosen: A2 — o manifest ja declara allowed/required context; o plano deriva dele
---

# Explore — ROLE_PLANS_SPAWN

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
