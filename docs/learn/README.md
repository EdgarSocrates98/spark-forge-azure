# Spark Forge Azure — trilha de aprendizado

| Nível | Caminho |
|---|---|
| **Iniciante** | [Quickstart](../installation/quickstart.md) → [first-run](../tutorials/first-run.md) → receita [primeiro uso](recipes/primeiro-uso.md) |
| **Intermediário** | [analyze](recipes/analyze-pyspark.md) → [doctor](recipes/doctor.md) → [diagnose Azure](recipes/analise-azure.md) → [fabric](recipes/fabric.md) → [streaming](recipes/streaming.md) → [migração](recipes/migration-assessment.md) → `graph` |
| **Avançado** | `lab` Forge Lab → `judge` rules → `collect`/`offline-bundle` → `sdd` gates → [economia](recipes/economia.md) |
| **Contribuidor** | [CONTRIBUTING](../../CONTRIBUTING.md) → `agents`/roster → `sparkforge-azure sdd` |
| **Agente (IA)** | [AGENTS](../../AGENTS.md) → `forge.agentic.json` workflows (`analyze`, `doctor`) → `--format json` |

## Receitas (problema → solução)

| Tenho este problema | Receita |
|---|---|
| "Fatos determinísticos do meu PySpark" | [analyze-pyspark](recipes/analyze-pyspark.md) |
| "Minha instalação está íntegra?" | [doctor](recipes/doctor.md) |
| "Como instalo o forge no meu projeto?" | [instalacao](recipes/instalacao.md) |
| "Qual o menor caminho real do forge?" | [primeiro-uso](recipes/primeiro-uso.md) |
| "Acesso negado em UC/ADLS/rede — qual camada?" | [analise-azure](recipes/analise-azure.md) |
| "Permissão/shortcut/pipeline do Fabric falhando" | [fabric](recipes/fabric.md) |
| "Pipelines ADF: migrar ou revisar?" | [adf](recipes/adf.md) |
| "Synapse: pool, pipeline ou migração?" | [synapse](recipes/synapse.md) |
| "Lag, exactly-once, Eventstream/Event Hubs" | [streaming](recipes/streaming.md) |
| "Vale migrar do ADF/Synapse pro Fabric?" | [migration-assessment](recipes/migration-assessment.md) |
| "Qual agente roteia essa tarefa?" | [usar-agents](recipes/usar-agents.md) |
| "Que skill cobre esse domínio?" | [usar-skills](recipes/usar-skills.md) |
| "O MCP do host está vivo de verdade?" | [verificar-mcp](recipes/verificar-mcp.md) |
| "O que quebra se eu mudar este dataset?" | [graphfy](recipes/graphfy.md) |
| "Bytes medidos vs tokens do provider" | [economia](recipes/economia.md) |
| "Meu host de IA está logado/integrado? abrir?" | [abrir-host](recipes/abrir-host.md) |

Hub do ecossistema (descoberta cross-forge): `the-forge/docs/hub/` — install, which-forge, hosts, MCP, troubleshooting.

Índice gerado: [../INDEX.md](../INDEX.md).
