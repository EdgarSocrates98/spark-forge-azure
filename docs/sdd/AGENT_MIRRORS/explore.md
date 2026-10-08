---
sdd: 1
feature: AGENT_MIRRORS
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: agents/*.md e a fonte unica; hosts leem direto
  tradeoffs:
  - zero codigo
  - hosts nao leem agents/ — exigem frontmatter name+description em .claude/agents
    ou .agents/agents
- id: A2
  summary: mirrors gerados file-per-agent com name/descricao injetados — mesmo regime
    dos skills mirrors (header GENERATED, drift missing|stale|orphan)
  tradeoffs:
  - disciplina ja provada
  - mais 80 arquivos gerados
chosen: A2 — §142 pede mirrors de agents no mesmo regime anti-drift das skills
---

# Explore — AGENT_MIRRORS

Skills tem mirrors em `.claude/skills/` + `.agents/skills/` gerados e travados
por teste de sync. Agents nao tem equivalente: `.claude/agents/custom/` e
`.agents/agents/` nao existem/vazios, entao os 40 manifests sao invisiveis aos
hosts. Manifest usa `id`/`mission`; host exige `name`/`description` — o render
injeta os dois.
