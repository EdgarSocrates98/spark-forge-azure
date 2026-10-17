# Spark Forge Azure

> Instalação: `pip install sparkforge-azure` (PyPI, Python >= 3.10). Instalação portátil/agentic: [`docs/installation/quickstart.md`](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/installation/quickstart.md) — clone → setup → install. Delegação agêntica: [forge.agentic.json](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/forge.agentic.json) (SpecialistAgenticManifest/v1).
> Docs: [commands](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/reference/commands.md) · [skills](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/reference/skills.md) · [agents](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/reference/agents.md) · [tutorial](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/tutorials/first-run.md) · [economy](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/economy.md) · [troubleshooting](https://github.com/EdgarSocrates98/spark-forge-azure/blob/v0.1.0/docs/installation/troubleshooting.md)

<p align="center">
  <img src="https://raw.githubusercontent.com/EdgarSocrates98/spark-forge-azure/v0.1.0/docs/assets/spark-forge-logo.jpg" alt="Logo do SparkForge" width="420">
</p>

**Plataforma de engenharia agentica para Data Engineering em Azure** — sibling
de `spark-forge-aws`. Inteligencia probabilistica opera dentro de limites
deterministicos, com evidencia e custo explicitos: Facts → Rules → Findings,
grafo federado de workspace, recusas nomeadas e um `journal` de decisoes
append-only (local, em `.sparkforge-azure/journal.jsonl`, fora do git).

- CLI: `sparkforge-azure` — uma saida JSON por comando, `0` ok, `1` findings, `2` recusa
- MCP: prefixo `sfa_`, allowlist, sem `execute`/`write` por padrao
- Portabilidade: `sparkforge-azure distribution init` integra um repo
  qualquer (instalado via wheel, sem checkout); `workspace` declara
  monorepo/multi-repo com arestas explicitas; `context resolve` devolve
  contexto bounded por scope (`target|direct|transitive|all`);
  `distribution detach` desfaz a integracao preservando estado e
  conteudo do usuario. Quickstart: `docs/guides/SPARKFORGE_AZURE_PORTABLE.md`
- Especificacao: SDD em `docs/sdd/` — `sdd-define` abre a feature e
  `sparkforge-azure sdd check` e o gate (no sibling AWS e `sparkforge sdd check`)

Documentacao completa: `docs/README.md` — CLI (`docs/reference/cli.md`),
tools MCP (`docs/reference/mcp-tools.md`), mapa de modulos
(`docs/architecture/MODULE-MAP.md`) e runbook (`docs/operations/runbook.md`).

Work in progress (v0.1.0 foundation). See docs/ROADMAP.md.

## Graph Studio

`sparkforge-azure graph view|ui` projects `graph.json` through
`forge/ForgeGraphView/v1` and serves the embedded local explorer (declinable at
install via `--components`). Full docs: `the-forge/docs/graph-studio/`.
