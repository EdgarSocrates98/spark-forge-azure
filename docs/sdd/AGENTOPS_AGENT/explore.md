---
sdd: 1
feature: AGENTOPS_AGENT
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Estender spans existentes com campos agent
  tradeoffs:
  - schema confunde stage e agent
- id: A2
  summary: AgentSpan proprio + AgentExecutionReceipt agregando considered/spawned/skipped
  tradeoffs:
  - span por execucao de agent
  - receipt por case
chosen: A2 — §56 exige campos de agent; §156 exige receipt de execucao
---

# Explore — AGENTOPS_AGENT

Alternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.
