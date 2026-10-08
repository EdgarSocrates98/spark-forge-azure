---
sdd: 1
feature: SKILL_HANDOFF_RESOLUTION
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Corrigir os dois `migration` e seguir
  tradeoffs:
  - rapido
  - a classe inteira de defeito continua passando
- id: A2
  summary: Corrigir + validador resolve alvos em skills ∪ ALL_AGENT_IDS
  tradeoffs:
  - classe fechada
  - lazy import por causa do ciclo agentmanifest→skills
chosen: A2 — handoff e superficie de contrato; alvo irresoluvel e defeito, nao estilo
---

# Explore — SKILL_HANDOFF_RESOLUTION

Auditoria das 22 skills: handoff `migration` em azure-synapse e iceberg nao
resolve para skill nem agent (`migration-specialist` e o alvo real). O
validador nunca confere alvos de handoff — a classe inteira passa.
