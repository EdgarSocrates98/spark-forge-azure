# Product Definition — Spark Forge Azure

> Fase 1 (§230). Fonte de verdade para escopo. Mudança aqui exige ADR.

## Missão

Agentic Engineering OS especializado em Azure Data Engineering: um sistema que **coleta
evidência, extrai fatos, aplica regras, consulta conhecimento versionado, usa grafos,
controla contexto, coordena especialistas e só usa modelos quando há ganho real** (§281).

Regra central: *probabilistic intelligence must operate inside deterministic,
evidence-backed, cost-aware engineering boundaries.*

## Personas

| Persona | Problema | O que o Forge entrega |
|---|---|---|
| **Data Engineer (Databricks/Fabric)** | job lento, OOM, skew, small files, MERGE regressivo | facts do código e de artefatos (event log, cluster JSON) → findings com evidência e mudança proposta |
| **Platform / Lakehouse Engineer** | acesso negado entre UC, ADLS, Entra e rede | diagnóstico multicamada de governança com cadeia de evidência e `unresolved` explícito |
| **Cloud / FinOps Engineer** | custo Databricks/Fabric/armazenamento sem atribuição | correlação compute×duração×tuning×storage×rede; nunca "X% de economia" sem baseline |
| **Tech Lead / Reviewer** | PR de PySpark/Terraform/Bicep/ADF sem revisão especializada | review determinístico + specialist sob budget |
| **Agente (Claude Code, Devin, Codex, Copilot)** | precisa de contexto mínimo e confiável | MCP compacto, TokenSave, RoleContextPlan, DATA_ONLY handoff |
| **Plataforma The Forger** | rotear tarefa Azure data | Forge Protocol: `provider=azure`, `domain=data`, capabilities |

## Casos de uso (v0.1.0)

1. `sparkforge-azure analyze pyspark --path repo/` → facts de código (AST, sem executar).
2. `sparkforge-azure judge --facts facts.json` → findings por regra versionada.
3. `sparkforge-azure governance diagnose --scenario ...` → conflitos RBAC/ACL/UC/rede.
4. `sparkforge-azure graph build|query|impact` → Graphfy do workspace multi-repo.
5. `sparkforge-azure tokensave search|read|symbols|refs|context` → retrieval econômico em escada.
6. `sparkforge-azure doctor` → saúde da instalação, sem tocar nuvem.
7. `sparkforge-azure lab run <scenario>` → Forge Lab sobre digital twin determinístico.
8. `sparkforge-azure offline-bundle` → pacote redigido para troca sem credenciais.
9. `sparkforge-azure mcp serve` → superfície MCP com risco declarado e compact mode.
10. `sparkforge-azure collect workspace-graph` → coleta read-only (Azure Resource Graph), opt-in.

## Não-objetivos

- Não é "LLM que sabe Azure" (§281). Sem modelo o núcleo funciona.
- Não muta nuvem por padrão. Operação destrutiva exige autorização explícita, classificação de
  risco, human gate e rollback (§208–§209).
- Não unifica CLIs entre Forges (§0) nem cria Forge Kernel (§192).
- Não antecipa GCP (§292).
- Não promete economia/segurança/suporte sem prova (§222–§224).
- Não substitui Azure Monitor/Purview/Cost Management — lê e correlaciona.
- AWS→Azure migration fora do MVP (§219).

## Plataformas suportadas

| Eixo | Suporte |
|---|---|
| Python | 3.10 – 3.14 (CI matrix 3.10/3.12/3.14) |
| SO | Linux, Windows (macOS best-effort) |
| Hosts de agente | Claude Code, Devin, Codex, GitHub Copilot (CLI/arquivos) |
| Azure | Databricks, Fabric, Synapse, ADF, ADLS Gen2, OneLake, Event Hubs, Purview, Entra, Key Vault, rede, Cost Management |
| Autenticação (opt-in) | DefaultAzureCredential, Azure CLI, Managed Identity, Service Principal, Workload Identity |

Offline sem autenticação é requisito (§179).

## Escopo Azure-first (v0.1.0 — §258)

Agentic OS · SDD · TokenSave · Graphfy · Code Intelligence · Workspace · MCP · CLI
`sparkforge-azure` · Spark genérico · ADLS · Entra foundation · **Databricks UC/ADLS
access vertical (deep — 10 cenários, evidence, grafo, agentops)** ·
Unity Catalog foundation · Fabric foundation · AgentOps · Forge Lab seed · security · supply chain.

Primeiro vertical que prova a arquitetura (§255): **PySpark + Azure Databricks + ADLS + Unity
Catalog + diagnóstico agentic + TokenSave + Code Intelligence + Graphfy + MCP**.

## Status de suporte (§224)

`SUPPORTED` · `PARTIAL` · `EXPERIMENTAL` · `PLANNED` · `NOT_APPLICABLE` — declarado por capability em
`parity.yaml` e `manifest.json`. Definição de pronto: §225 (contract + implementation + runtime
integration + policy + tests + eval + observability + docs + evidence). Arquivo existir ≠ pronto (§167).
