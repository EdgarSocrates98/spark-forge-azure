---
id: azure.cosmosdb.change-feed
title: Change Feed do Cosmos DB no Spark - CDC streaming e batch, startFrom, modos, checkpoint e backpressure
domain: azure-cosmos-db
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed-spark
    retrieved: 2026-11-03
  - url: https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed
    retrieved: 2026-11-03
verified_at: 2026-11-03
versions: {azure-cosmos-spark_3-5_2-12: ["4.29.0-4.50.0"]}
status: VERIFIED
preview: false
related: [azure.cosmosdb.spark-connector, azure.cosmosdb.bulk-and-batch, azure.spark.streaming-state-checkpoint, agentic.evidence-first]
---

# Change Feed (CDC) do Cosmos DB via Spark

Fonte `cosmos.oltp.changeFeed`: **somente leitura**, usável em `readStream` (Structured
Streaming) e em `read` batch. Não confundir com Delta Change Data Feed (`delta-lake`) nem
com o Change Feed Processor do SDK — aqui o paralelismo vem dos feed ranges mapeados em
partições Spark.

## Posição inicial (`spark.cosmos.changeFeed.startFrom`)

- `Beginning` (default): todo o histórico retido do contêiner.
- `Now`: apenas mudanças a partir do início do stream.
- Timestamp UTC ISO-8601 (ex.: `2020-02-10T14:15:03`): ponto específico.
- **Precedência do checkpoint**: se `checkpointLocation` já contém estado, o stream sempre
  continua de lá — `startFrom` é ignorado. Para reprocessar do início, trocar o
  checkpointLocation ou apagar os checkpoints.

## Modos (`spark.cosmos.changeFeed.mode`)

- `Incremental/LatestVersion` (default): última versão de cada item; **não** entrega
  deletes nem versões intermediárias entre polls.
- `FullFidelity/AllVersionsAndDeletes` — **PREVIEW/experimental** segundo o reference:
  exige habilitação no nível da conta (private preview), entrega todas as versões +
  deletes, e há breaking changes conhecidos no schema retornado. Recomendado apenas para
  cenários não-produtivos.

## Controle de vazão e backpressure

- `spark.cosmos.changeFeed.itemCountPerTriggerHint`: máximo aproximado de itens por
  micro-batch. **Sem o hint, todo o backlog disponível entra no primeiro micro-batch** —
  risco real de OOM de executor no catch-up inicial; o reference sugere ordem de
  centenas de milhares a milhões conforme memória.
- `spark.cosmos.changeFeed.performance.monitoring.enabled` (default `true`): task metrics
  internos alimentam o ajuste dinâmico do tamanho do micro-batch.
- `spark.cosmos.read.partitioning.strategy=Restrictive` reduz o número de partições Spark
  em cenários de pouco paralelismo de feed range.
- `spark.cosmos.changeFeed.batchCheckpointLocation`: gera checkpoint em leitura batch de
  change feed — permite retomar na iteração seguinte de onde parou (CDC incremental em
  jobs agendados, sem Structured Streaming).

## Semânticas — o que NÃO afirmar sem evidência

- Checkpoint do Spark garante recomeço do ponto; a entrega final depende do sink —
  **não afirmar exactly-once** sem sink idempotente + esquema de dedup provado
  (`azure.spark.streaming-state-checkpoint`).
- Change feed Cosmos não retém deletes no modo LatestVersion: pipelines que exigem tombstone
  precisam de soft-delete no documento ou do modo FullFidelity (PREVIEW).
- Retenção do change feed é limitada pelo ponto mais antigo disponível no contêiner;
  restart além da janela pode perder mudanças — evidenciar `startFrom` + lag antes de
  garantir completude.
- Schema drift entre versões de documento chega ao DataFrame; tratar com
  `read.schemaConversionMode` (`Relaxed` default / `Strict`) e política explícita.

## Diagnóstico

- Lag = diferença entre posição do checkpoint e head do feed; medir por métricas do job +
  logs, não por tempo de query.
- Throughput do change feed consome RU do contêiner de origem: em contêiner saturado, isolar
  com throughput control dedicado (ver `azure.cosmosdb.model-and-limits`).
- Handoffs: micro-batch/checkpoint/trigger → `spark-streaming`; controle de RU/429 →
  `azure.cosmosdb.model-and-limits` + throughput control.

## Fontes

- https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed-spark (retrieved: 2026-11-03)
- https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed (retrieved: 2026-11-03)
