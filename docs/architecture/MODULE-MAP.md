# Mapa de módulos — `sparkforge_azure`

Cada pacote em uma linha, agrupado pela camada do ADR-0001 (L0–L8). As arestas
reais entre pacotes são medidas por `tests/test_architecture_layers.py`.

## L0 kernel — folhas (não importam nada do pacote)

| Pacote | Papel |
|---|---|
| `paths` | confinamento de caminho — UMA implementação para todos |
| `durable` | escrita que sobrevive a queda no meio (estado nunca pela metade) |
| `protocols` | protocolos públicos provider-neutral (Forge Protocol, A2A experimental) |
| `findings` | contratos Fact/Finding/RuntimeContext — a folha do pipeline |

## L2 engines — motores determinísticos

| Pacote | Papel |
|---|---|
| `rules` | catálogo de regras + roteamento (Facts → Rules → Findings) |
| `decision` | kernel de decisão bounded, provider-independent |
| `context` | engenharia de contexto (fatias, orçamento, gateway por agente) |
| `economy` | Economy Engine: ledgers de token/contexto, reconciliação, cache, profiles |
| `tokensave` | escada de recuperação econômica L0–L6 |
| `codeintel` | índice local de código — offline, sem dependência externa |
| `knowledgebase` | base knowledge versionada: contrato, frescor, matrizes, expansão |
| `knowledge_engine` | compiler offline + domain packs demand-loaded |
| `knowledge_drift` | radar: o que uma fonte vigiada que mudou arrasta |
| `knowledge_freshness` | estado de frescor de cada fonte citada |
| `knowledge_ref` | localização confinada dos arquivos `knowledge/` |
| `facts` | extração de facts (observação sem juízo) |
| `collect` | **port** neutro de coleta — isola `collectors` (L6) dos engines |
| `policy` | política de segurança declarada `.sparkforge-azure/policy.yaml` |
| `proof` | obrigações de prova de uma mudança aplicada |
| `simulate` | simulação determinística (digital twin básico) |

## L3 graph

| Pacote | Papel |
|---|---|
| `graph` | Graphfy: grafo semântico/workspace — estático, live, federação, impacto |
| `workspace` | workspace multi-repo declarado + grafo semântico determinístico |

## L4 agentic — runtime e orquestração

| Pacote | Papel |
|---|---|
| `agentic` | runtime agentic: governor, budget, stop, recovery, memory, checkpoint, router |
| `agentmanifest` | manifests de agent/specialist + roteamento determinístico |
| `agents` | despacho/autonomia de especialistas |
| `registry` | registro canônico (agents, skills, manifests) |
| `case` | o case: fases, store durável, playbook, router, resume |
| `receipt` | Execution Receipt content-addressed de uma execução |
| `change` | autonomia L1-L2: `plan` a mudança + `sandbox` numa cópia |
| `skills` | SKILL.md contrato v1, mirrors de host, seleção determinística |
| `evals` | harness de avaliação (fixtures, goldens, métricas) |
| `adapters` | tools `sfa_*` do harness de evals agenticos (módulo Azure novo) |
| `sdd` | SDD próprio: contrato conferível dos artefatos de spec |

## L5 domain + L6 collectors

| Pacote | Papel |
|---|---|
| `azure` | camada de domínio Azure (L5) — camadas baixas nunca a importam |
| `fabric` | vertical Fabric (L5) — diagnose OneLake/Spark/capacity/RTI-seam |
| `stream` | vertical Streaming/RTI (L5) — Event Hubs, progress, correctness, RTI |
| `migration` | vertical migração ADF/Synapse→Fabric (L5) — assessment evidence-bound |
| `collectors` | coletores Azure read-only com redaction obrigatória (L6) |

## L7 surfaces

| Pacote | Papel |
|---|---|
| `cli` | o binário `sparkforge-azure` (um JSON por comando) |
| `mcp` | superfície MCP: registry de tools, envelope, server |
| `doctor` | `sparkforge-azure doctor` — saúde sem acesso à nuvem |
| `bundle` | offline bundle portátil e redigido |
| `lab` | Forge Lab / Digital Twin offline + contratos de produto |

## L8 assurance

| Pacote | Papel |
|---|---|
| `observability` | Observability + AgentOps: surface lock, spans OTel |
| `packs` | Forge Pack: regras/knowledge/fixtures de terceiro junto do core |

## Notas de aresta (medidas, com razão)

- `context→agentic`, `economy→agentic`, `receipt→agentic` — engines consomem
  contratos do runtime via import preguiçoso; a exceção é declarada no teste.
- `adapters` — nome colide com o pacote AWS de adapters MCP (30k LOC, 914
  marcadores) que **não** foi portado; aqui é módulo novo do harness de evals
  (`new_azure` em `parity.yaml`).
- `__init__` — identidade `sparkforge_azure.__version__`; o `__init__` AWS não
  foi portado.
