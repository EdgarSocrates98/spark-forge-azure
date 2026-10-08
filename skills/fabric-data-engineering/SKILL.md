---
name: fabric-data-engineering
description: 'Use para Microsoft Fabric: Lakehouse, notebooks Spark, Spark job definitions, environments,
  pipelines do Data Factory do Fabric e Dataflow Gen2. Sintomas: notebook lento no Fabric, environment
  com biblioteca divergente, pipeline do Fabric falhando, ''Lakehouse ou Warehouse?''. Fabric não é Synapse
  e Data Factory do Fabric não é ADF: artefatos, APIs e limites diferem.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - fabric
  - fabric lakehouse
  - fabric notebook
  - spark job definition
  - dataflow gen2
  - fabric pipeline
  - fabric environment
  scope:
  - Microsoft Fabric
  - Lakehouse
  - Fabric notebooks
  - Spark job definitions
  - Fabric environments
  - Data Factory do Fabric
  does:
  - lê definições de item Fabric e código de notebook offline
  - compara environment (bibliotecas, Spark conf) com o código
  - revisa pipelines do Data Factory do Fabric como artefatos próprios
  does_not:
  - não cobre Azure Synapse (azure-synapse)
  - não trata pipeline do Fabric como pipeline ADF (azure-data-factory)
  - não detalha segurança OneLake (fabric-onelake) nem RTI (fabric-realtime)
  knowledge_refs:
  - knowledge/azure/fabric/
  - knowledge/spark/
  tool_refs:
  - sparkforge-azure analyze fabric-item
  - sparkforge-azure analyze pyspark
  - sparkforge-azure graph impact
  - sfa_analyze
  - sfa_graph_impact
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/fabric-data-engineering/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# Fabric Data Engineering

Workloads de engenharia de dados do Microsoft Fabric. Fabric tem artefatos e limites próprios; nada é herdado de Synapse ou ADF por analogia.

## Quando usar

- `fabric`
- `fabric lakehouse`
- `fabric notebook`
- `spark job definition`
- `dataflow gen2`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — definições de item exportadas (Git integration/REST), código de notebook, environment YAML, pipeline JSON do Fabric, export de capacity metrics. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze fabric-item --path fabric-workspace/ --out .sparkforge-azure/facts.json
sparkforge-azure analyze pyspark --path fabric-workspace/notebooks/
sparkforge-azure graph impact --node fabric:<item-guid>
```

   Fatos esperados:
   - tipo e GUID de cada item (Lakehouse, Notebook, SparkJobDefinition, DataPipeline)
   - environment anexado e bibliotecas/Spark conf declaradas
   - atividades do pipeline do Fabric e conexões referenciadas
   - capacidade (SKU) declarada no export, se houver
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain fabric-data-engineering`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — composição só por GUID de workspace/item; nome parecido entre workspaces não é o mesmo item.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Fabric não é Synapse: artefato de workspace Synapse → `azure-synapse`, não esta skill.
- Pipeline é ADF (ARM export com `Microsoft.DataFactory`) → `azure-data-factory`.
- Acesso a shortcut/arquivo OneLake → `fabric-onelake`.
- Eventstream/Eventhouse → `fabric-realtime`; throttling de capacidade → `azure-finops`.

## Não concluir sem evidência

- Não afirmar comportamento do Fabric a partir de documentação do Synapse.
- Não tratar o Data Factory do Fabric como ADF.
- Não declarar capacidade "suficiente" sem métricas de capacidade exportadas.
- Não prometer economia ao mudar SKU sem baseline.

## Fronteiras

- Não cobre Azure Synapse (azure-synapse).
- Não trata pipeline do Fabric como pipeline ADF (azure-data-factory).
- Não detalha segurança OneLake (fabric-onelake) nem RTI (fabric-realtime).

## Handoff

- `fabric-onelake` — acesso, shortcut ou segurança OneLake.
- `fabric-realtime` — Eventstream, Eventhouse, KQL.
- `azure-finops` — capacidade, CU, throttling, custo.
- `spark-performance` — lentidão de Spark com evidência de execução.
- `azure-databricks` / `unity-catalog` — notebook, grant ou ACL fora do
  Fabric (Databricks + UC).

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
