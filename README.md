# Spark Forge Azure

<p align="center">
  <img src="docs/assets/spark-forge-logo.jpg" alt="Logo do SparkForge" width="420">
</p>

**Plataforma de engenharia agentica para Data Engineering em Azure** — sibling
de `spark-forge-aws`. Inteligencia probabilistica opera dentro de limites
deterministicos, com evidencia e custo explicitos: Facts → Rules → Findings,
grafo federado de workspace, recusas nomeadas e um `journal` de decisoes
append-only (local, em `.sparkforge-azure/journal.jsonl`, fora do git).

- CLI: `sparkforge-azure` — uma saida JSON por comando, `0` ok, `1` findings, `2` recusa
- MCP: prefixo `sfa_`, allowlist, sem `execute`/`write` por padrao
- Especificacao: SDD em `docs/sdd/` — `sdd-define` abre a feature e
  `sparkforge-azure sdd check` e o gate (no sibling AWS e `sparkforge sdd check`)

Documentacao completa: `docs/README.md` — CLI (`docs/reference/cli.md`),
tools MCP (`docs/reference/mcp-tools.md`), mapa de modulos
(`docs/architecture/MODULE-MAP.md`) e runbook (`docs/operations/runbook.md`).

Work in progress (v0.1.0 foundation). See docs/ROADMAP.md.
