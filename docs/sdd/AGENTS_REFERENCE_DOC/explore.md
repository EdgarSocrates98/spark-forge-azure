---
sdd: 1
feature: AGENTS_REFERENCE_DOC
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: doc autoral de agents
  tradeoffs:
  - deriva — AGENT_INVENTORY ja prova que doc autoral fica stale
- id: A2
  summary: docs/reference/agents.md gerado de agents/*.md (mesmo regime de skills.md)
  tradeoffs:
  - anti-drift comprovado
  - mais um artefato gerado
chosen: A2 — par do skills.md; generated never stale
---

# Explore — AGENTS_REFERENCE_DOC

`docs/reference/` tem skills.md gerado; agents so tem AGENT_INVENTORY.md (status). Falta o catalogo de capacidade: kind/domain/autonomy/evals/mirrors por agent.
