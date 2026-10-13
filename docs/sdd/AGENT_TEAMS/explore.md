---
sdd: 1
feature: AGENT_TEAMS
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Teams hardcoded em python
  tradeoffs:
  - config deveria ser dado
  - spec pede arquivo
- id: A2
  summary: 'agent-teams/*.yaml: eligible + rules, runtime decide subconjunto'
  tradeoffs:
  - declarativo
  - auditavel
chosen: A2 — arquivo define elegibilidade; runtime compoe dinamicamente
---

# Explore — AGENT_TEAMS

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
