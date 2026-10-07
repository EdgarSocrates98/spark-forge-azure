---
name: azure-synapse
description: 'Use para Azure Synapse Analytics: Spark pools, pipelines do Synapse, dedicated e serverless
  SQL pools, linked services e workspace Synapse. Sintomas: Spark pool com versão fora de suporte, autopause/autoscale,
  pipeline Synapse falhando, ''migrar Synapse para Fabric ou Databricks?''. Synapse não é Fabric; o caminho
  de migração vai para o migration specialist.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - synapse
  - spark pool
  - dedicated sql pool
  - serverless sql pool
  - synapse pipeline
  - synapse workspace
  scope:
  - Azure Synapse
  - Synapse Spark pools
  - Synapse pipelines
  - dedicated SQL pool
  - serverless SQL pool
  - linked services
  does:
  - lê Spark pool JSON (versão, autoscale, autopause, node size)
  - lê pipelines e linked services do Synapse
  - levanta fatos de inventário para migração
  does_not:
  - não cobre Microsoft Fabric (fabric-data-engineering)
  - não decide plano de migração (migration specialist)
  - não otimiza consultas T-SQL do dedicated pool em profundidade
  knowledge_refs:
  - knowledge/azure/synapse/
  - knowledge/migration/
  tool_refs:
  - sparkforge-azure analyze synapse-spark-pool
  - sparkforge-azure analyze synapse-pipeline
  - sparkforge-azure graph build
  - sfa_analyze
  - sfa_graph_query
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-synapse/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# Azure Synapse Analytics

Workspace Synapse e seus runtimes. Artefatos do Synapse são lidos como Synapse — não como Fabric nem como ADF.

## Quando usar

- `synapse`
- `spark pool`
- `dedicated sql pool`
- `serverless sql pool`
- `synapse pipeline`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — Spark pool JSON, pipeline JSON do Synapse, linked services, definição de SQL pools, notebooks do workspace. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze synapse-spark-pool --path synapse/sparkpools/ --out .sparkforge-azure/facts.json
sparkforge-azure analyze synapse-pipeline --path synapse/pipelines/
sparkforge-azure graph build --path synapse/
```

   Fatos esperados:
   - versão do Spark pool e status de suporte no knowledge
   - autoscale/autopause e node size
   - atividades de pipeline e linked services usados
   - dependências notebook ↔ pipeline ↔ linked service
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-synapse`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — IDs de recurso ARM do workspace conferidos; versão de runtime comparada com knowledge datado.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Synapse não é Fabric: pergunta de migração → `migration` specialist com o inventário produzido aqui.
- Pipeline é ADF de verdade (factory separada) → `azure-data-factory`.
- Spark lento com evidência → `spark-performance`.
- Acesso a storage → `azure-adls`.

## Não concluir sem evidência

- Não afirmar que algo do Synapse funciona igual no Fabric.
- Não declarar paridade de migração sem inventário completo.
- Não afirmar suporte de runtime sem data de referência do knowledge.
- Não prometer redução de custo pós-migração sem baseline.

## Fronteiras

- Não cobre Microsoft Fabric (fabric-data-engineering).
- Não decide plano de migração (migration specialist).
- Não otimiza consultas T-SQL do dedicated pool em profundidade.

## Handoff

- `migration` — decisão ou plano de migração.
- `azure-data-factory` — factory ADF separada.
- `spark-performance` — lentidão de Spark com evidência.
- `azure-adls` — acesso a storage.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
