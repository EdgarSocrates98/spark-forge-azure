---
name: azure-cosmos-db
description: 'Use para Azure Cosmos DB for NoSQL e seu conector Spark (cosmos.oltp /
  cosmos.oltp.changeFeed): leitura, bulk load e cargas batch, CDC via change feed,
  throughput/RU, partition keys, autenticação e matriz de versões do conector.
  Sintomas: 429/throttling, bulk lento, hot partition, change feed acumulando,
  leitura cara em RU, conector incompatível com o runtime Spark. Não decide semântica
  de checkpoint do Spark nem tuning genérico de engine.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - cosmos
  - cosmos db
  - cosmosdb
  - change feed
  - request unit
  - partition key
  - bulk load
  - '429'
  - throughput control
  scope:
  - Azure Cosmos DB for NoSQL
  - conector Spark azure-cosmos-spark_3-*
  - leitura/partitioning/pushdown
  - bulk e batch writes
  - change feed (CDC)
  - RU, throughput control, partition keys
  does:
  - lê config spark.cosmos.* e opções do conector no código/notebook
  - verifica compatibilidade conector × Spark × Scala × DBR/Fabric pela matriz oficial
  - classifica escrita (bulk/point, estratégia Item*), leitura (partitioning strategy) e CDC (startFrom/mode)
  - 'mapeia sintoma de RU (429, throttle) para camada — RU total, hot partition, throughput control'
  does_not:
  - não executa escritas nem muta conta/banco/contêiner
  - não cobre APIs Mongo/Cassandra/Gremlin/Table nem conector OLAP do Synapse Link
  - não decide semântica de checkpoint/exactly-once do Spark (spark-streaming)
  - não faz tuning genérico de engine Spark (spark-performance)
  knowledge_refs:
  - knowledge/azure/cosmosdb/
  tool_refs:
  - sparkforge-azure analyze pyspark
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze cosmos-config
  - sparkforge-azure analyze cosmos-account
  eval_refs:
  - skills/azure-cosmos-db/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# Azure Cosmos DB for NoSQL (conector Spark)

Banco NoSQL distribuído cobrado em RU/s. O conector `azure-cosmos-spark_3-*` expõe
`cosmos.oltp` (leitura/escrita) e `cosmos.oltp.changeFeed` (CDC somente leitura).
Toda conclusão sobre RU, partições e semântica exige config + métrica, nunca suposição.

## Quando usar

- `cosmos`, `cosmos db`, `cosmosdb`, `azure cosmos`
- `cosmos.oltp`, `change feed`, `partition key`, `request unit`, `ru/s`
- `bulk load`, `bulk write`, `429`, `throughput control`, `integrated cache`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — código/notebook com `spark.cosmos.*`, opções do DataFrame,
   versão do conector e do runtime Spark, export de métricas Cosmos (RU, throttles)
   quando houver. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze pyspark --path <repo> --out .sparkforge-azure/facts.json   # opções spark.cosmos.* no código
# Sem extrator dedicado ainda (planned_tool_refs): fatos de conta/contêiner
# (RU provisionado, partition key, indexing) completam o facts.json montados do export.
```

   Fatos esperados:
   - versão do artefato `azure-cosmos-spark_*` × Spark × Scala × DBR/Fabric (matriz do README)
   - `write.strategy` (default `ItemOverwrite`), `write.bulk.enabled` (default `true`) e knobs de lote
   - `read.partitioning.strategy`, `customQuery`, `inferSchema`, filtros de partition key
   - change feed: `startFrom`, `mode`, `itemCountPerTriggerHint`, `checkpointLocation`
   - auth (`MasterKey`/`ServicePrincipal`/`ManagedIdentity`) e segredos em código
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-cosmos-db`;
   usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json`
   gera findings com regra versionada e evidência.
5. **Verificar** — opção citada existe na referência oficial de configuração; limite citado
   tem URL e `verified_at`; PREVIEW marcado.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- 429/throttling → medir RU: teto do contêiner, hot partition (10K RU/s por partição)
  ou falta de throughput control? Métrica decide, não o palpite.
- Bulk lento → `write.bulk.enabled`? distribuição de partition key no lote? throughput
  control isolando a carga? Concorrência auto (VM) vs `maxPendingOperations`.
- Change feed acumulando → `itemCountPerTriggerHint` ausente (primeiro micro-batch pega
  todo o backlog)? checkpoint vs `startFrom`? modo `LatestVersion` vs
  `AllVersionsAndDeletes` (PREVIEW)?
- Leitura cara → projeção/pushdown, `partitioning.strategy`, `feedRangeFilter`,
  `readManyFiltering`, integrated cache (0 RU só com repetição).
- Versão do conector → artefato `3-5/3-4/3-3` tem que casar com Spark/Scala/DBR; Fabric só
  a partir de 4.41.0 no artefato 3-5.
- Checkpoint/duplicidade/watermark no consumidor Spark → `spark-streaming`.
- Skew/shuffle/spill/OOM de executor → `spark-performance`.
- Service principal, managed identity, segredo no código → `azure-entra`.
- Private endpoint, DNS `privatelink.documents.azure.com`, firewall → `azure-networking`.
- Runtime DBR/Fabric, instalação Maven, cluster → `azure-databricks`.

## Não concluir sem evidência

- Não afirmar RU suficiente nem throttling sem métrica (NormalizedRUConsumption, 429, diagnostics).
- Não prometer throughput/latência sem baseline medido no mesmo caso.
- Não afirmar exactly-once pelo change feed — depende do sink; ver `spark-streaming`.
- Não afirmar modo `FullFidelity/AllVersionsAndDeletes` pronto para produção: é PREVIEW.
- Não afirmar suporte a Managed Identity fora de Databricks/HDInsight sem fonte.
- Não expor `accountKey`/client secrets; citar só localização do segredo.
- Não tratar número sem fonte: limite e versão exigem URL oficial + `verified_at`.

## Fronteiras

- Só API for NoSQL: Mongo, Cassandra, Gremlin, Table e `cosmos.olap` (Synapse Link)
  estão fora; Fabric mirroring também.
- Não executa writes nem muta conta/banco/contêiner (cloud mutation: default deny).
- Não confunde change feed Cosmos com Delta Change Data Feed (delta-lake).
- Não decide semântica de checkpoint/trigger do Spark (spark-streaming) nem tuning de
  engine genérico (spark-performance).

## Handoff

- `spark-streaming` — checkpoint, trigger, watermark, semântica de entrega do sink.
- `spark-performance` — skew, spill, OOM, shuffle no job que usa Cosmos.
- `azure-entra` — ServicePrincipal, ManagedIdentity, segredos e RBAC de dados.
- `azure-networking` — private endpoint, DNS, firewall da conta Cosmos.
- `azure-databricks` — runtime DBR, instalação do pacote Maven, cluster/policy.
- `azure-event-hubs` — fonte Kafka/Event Hubs do stream (não é Cosmos).

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
