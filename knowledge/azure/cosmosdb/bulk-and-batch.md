---
id: azure.cosmosdb.bulk-and-batch
title: Carga em massa e batch no Cosmos DB via conector Spark - bulk mode, estratégias de escrita, sizing e retries
domain: azure-cosmos-db
authority: microsoft_official
sources:
  - url: https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md
    retrieved: 2026-11-03
  - url: https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/scenarios/Ingestion.md
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/transactional-batch
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-control-spark
    retrieved: 2026-11-03
verified_at: 2026-11-03
versions: {azure-cosmos-spark_3-5_2-12: ["4.29.0-4.50.0"]}
status: VERIFIED
preview: false
related: [azure.cosmosdb.spark-connector, azure.cosmosdb.model-and-limits, azure.cosmosdb.change-feed, azure.spark.execution-model]
---

# Bulk load e cargas batch no Cosmos DB (conector Spark)

## Bulk mode (default ligado)

- `spark.cosmos.write.bulk.enabled` (default `true`): agrupa operações por partição física e
  envia micro-lotes; desligar só para workloads de poucos itens ou requisito de latência
  por operação.
- `spark.cosmos.write.bulk.maxPendingOperations` (default: derivado do tamanho da VM do
  executor): limite de operações concorrentes no bulk; a recomendação do reference para
  cargas grandes é a estimativa `1000 x núcleos` do executor.
- `spark.cosmos.write.point.maxConcurrency` (default: derivado da VM): concorrência quando
  bulk está desligado.
- `spark.cosmos.write.bulk.targetedPayloadSizeInBytes` (default `220201` ≈ 215 KB, otimizado
  para documentos ≤10 KB): para documentos >110 KB pode subir até ~`1500000` (<2 MB).
- `spark.cosmos.write.bulk.initialBatchSize` (default `100`): tamanho inicial do micro-lote;
  o lote é auto-ajustado pela taxa de throttling. Reduzir para não gastar RUs demais nas
  primeiras requisições.
- `spark.cosmos.write.bulk.maxBatchSize` (default `100`): usar apenas ao migrar workloads
  do Spark 2.4; nos demais casos confiar no auto-tuning + throughput control.
- `spark.cosmos.write.maxRetryCount` (default `10`): retries em falhas passíveis de retry.
- `spark.cosmos.write.flush.noProgress.maxIntervalInSeconds` (default `180`): sem progresso
  no bulk, reinicializa o writer; tolera eventos transitórios como partition split/merge.
- `spark.cosmos.write.flush.noProgress.maxRetryIntervalInSeconds` (default `2700` = 45 min):
  teto total sem progresso antes de falhar o job.

## Estratégias de escrita (`spark.cosmos.write.strategy`)

| Estratégia | Semântica |
|---|---|
| `ItemOverwrite` (default) | upsert |
| `ItemOverwriteIfNotModified` | etag vazio → insert; etag presente → replace condicionado; conflito pula o item |
| `ItemAppend` | create; ignora itens pré-existentes (conflict 409 → skip) |
| `ItemDelete` / `ItemDeleteIfNotModified` | delete total / delete só se etag não mudou |
| `ItemPatch` / `ItemPatchIfExists` | update parcial; `ItemPatch` falha em 404, `ItemPatchIfExists` pula |
| `ItemBulkUpdate` | read → patch local → create/replace com etag; retenta em conflito |

Patch é configurável por `spark.cosmos.write.patch.defaultOperationType` (default `Replace`;
opções `none/add/set/replace/remove/increment`), `spark.cosmos.write.patch.columnConfigs`
(`col(x).op(t)` ou `col(x).path(/cosmos/path).op(t)`) e `spark.cosmos.write.patch.filter`
(patch condicional; 412 Precondition Failed vira no-op).

## Transactional bulk (`spark.cosmos.write.bulk.transactional`)

- **PREVIEW/condicional**: exige Spark 3.5+; somente upsert; agrupa por partition key e
  executa atomicamente (tudo ou nada). Limite de serviço: **100 operações e 2 MB** por
  lote transacional (mesmo limite do Transactional Batch do serviço).
- Em contêineres com partition key hierárquica (HPK), o escopo transacional é a **partição
  lógica completa** (caminho inteiro), não o nível superior parcial.
- `spark.cosmos.write.bulk.transactional.maxOperationsConcurrency` (default `100`) e
  `.maxBatchesConcurrency` (default `5`, faixa 1–5) controlam o paralelismo intra-partição;
  aumentar eleva paralelismo e consumo de RU — e o risco de throttling.

## Sizing de RU para carga em massa

- O consumo é limitado por RU/s provisionado **e** por RU/s por partição física
  (ver `azure.cosmosdb.model-and-limits`): distribuição uniforme de partition keys no lote é
  pré-requisito para escoar vazão — carga concentrada em poucas PKs estrangela no limite
  por partição, não no limite do contêiner.
- Isolar a carga com throughput control (ver `azure.cosmosdb.model-and-limits`): grupo
  client-side com `targetThroughput`/`targetThroughputThreshold` ou bucket server-side
  (`throughputBucket`, PREVIEW).
- Em 429 persistente: evidência vem do rate de throttling (métrica NormalizedRUConsumption /
  throttle diagnostics), não do tempo de job — medir antes de aumentar RU/s.
- Cargas iniciais grandes: combinar bulk + autoscale max alto (ou elevar RU/s manualmente
  durante a janela) + `initialBatchSize` baixo nas primeiras execuções.
- `spark.cosmos.serialization.inclusionMode` (default `Always`) e
  `serialization.dateTimeConversionMode` afetam payload e compatibilidade do documento
  gravado — fixar explicitamente quando o item já tem schema em produção.

## Fontes

- https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md (retrieved: 2026-11-03)
- https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/scenarios/Ingestion.md (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/transactional-batch (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-control-spark (retrieved: 2026-11-03)
