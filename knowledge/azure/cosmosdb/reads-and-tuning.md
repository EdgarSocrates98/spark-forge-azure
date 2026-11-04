---
id: azure.cosmosdb.reads-and-tuning
title: Leitura e tuning Spark com Cosmos DB - partitioning strategy, pushdown, readMany, schema inference e diagnóstico de RU
domain: azure-cosmos-db
authority: microsoft_official
sources:
  - url: https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/integrated-cache
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/dedicated-gateway
    retrieved: 2026-11-03
verified_at: 2026-11-03
versions: {azure-cosmos-spark_3-5_2-12: ["4.29.0-4.50.0"]}
status: VERIFIED
preview: false
related: [azure.cosmosdb.spark-connector, azure.cosmosdb.model-and-limits, azure.spark.performance-aqe-shuffle-skew, azure.spark.execution-model]
---

# Leitura e tuning do conector Spark com Cosmos DB

## Partitioning strategy (`spark.cosmos.read.partitioning.strategy`)

| Estratégia | Uso |
|---|---|
| `Default` (default) | conector calcula o número de partições Spark a partir dos feed ranges físicos |
| `Restrictive` | menos partições Spark que o default — reduz overhead em leituras pequenas |
| `Aggressive` | mais partições Spark — mais paralelismo por task em leituras grandes |
| `Custom` | número fixo via `spark.cosmos.partitioning.targetedCount` (ignorado nas outras) |

- `spark.cosmos.partitioning.feedRangeFilter`: limita a leitura a uma (ou poucas)
  partições lógicas — reduz SparkTasks/partições quando o escopo é conhecido.
- Partições Spark × executores × RU disponível é o balanço central: muitas partições com
  RU insuficiente só aumenta 429/fila; medir RU consumida antes de subir agressividade.

## Pushdown e queries

- O conector faz predicate pushdown dos filtros do plano Spark; projeção reduz RU.
- `spark.cosmos.read.customQuery`: fallback para predicados que o pushdown **não** cobre —
  agregações (count, group by, avg, sum) não são pushable (documentado para Spark 3.1);
  com schema inference ligada, a custom query também infere o schema.
- `spark.cosmos.read.maxItemCount` (default `1000`): itens por página; subir só com
  documentos ≪1 KB ou projeção muito pequena.
- `spark.cosmos.read.responseContinuationTokenLimitInKb` (mín. `1`): limita o token de
  continuação quando headers estouram.
- `spark.cosmos.read.runtimeFiltering.enabled` (default `true`): dynamic partition pruning
  pushdown quando aplicável.
- `spark.cosmos.read.readManyFiltering.enabled` (default `false`): usa `ReadMany` em vez de
  query quando o filtro casa com a propriedade de filtro — `id` se PK=`id`, senão
  `_itemIdentity` (UDF `GetCosmosItemIdentityValue(id, pk)` ou `(id, array(pk1,pk2,pk3))`
  em subpartições).
- Consultas cross-partition sem filtro de PK varrem todos os feed ranges: preferir filtro
  por partition key + `feedRangeFilter` quando o escopo for uma partição lógica.

## Schema e serialização na leitura

- `spark.cosmos.read.inferSchema.enabled` (default `true`): amostragem
  `inferSchema.samplingSize` (default `1000`) ou `inferSchema.query` (default
  `SELECT * FROM r`) — com múltiplas entidades no mesmo contêiner, restringir a query de
  inferência ao tipo desejado.
- `inferSchema.includeSystemProperties`/`includeTimestamp` (default `false`) para `_ts`
  e demais propriedades de sistema; `forceNullableProperties` (default `true`).
- `read.schemaConversionMode`: `Relaxed` (default, tipo divergente → null) vs `Strict`
  (→ exceção) — escolher conforme tolerância a schema drift.
- `read.allowInvalidJsonWithDuplicateJsonProperties` (default `false`): workaround
  temporário para JSON inválido — o reference recomenda corrigir a ingestão, não deixar ligado.
- `serialization.dateTimeConversionMode`: `Default` (comportamento Spark 3.x: Date→EpochDay,
  Timestamp→Micros) vs `AlwaysEpochMilliseconds` (semântica do conector Spark 2.4) vs
  `...WithSystemDefaultTimezone` — fixar ao migrar pipelines 2.4 com datas.

## Consistência, gateway e cache

- `spark.cosmos.read.forceEventualConsistency` (default `true`): leituras eventual mesmo em
  conta com default mais forte. `read.consistencyStrategy` (`EVENTUAL`, `DEFAULT`,
  `SESSION`, `LOCAL_COMMITTED`) sobrepõe — **PREVIEW**; em Gateway mode só `DEFAULT` e
  `EVENTUAL`.
- `spark.cosmos.useGatewayMode` (default `false`): força modo gateway (contra direct TCP).
- `spark.cosmos.read.maxIntegratedCacheStalenessInMS`: staleness aceito no cache integrado
  do dedicated gateway — hit de item/query cache tem custo **0 RU** (ver integrated cache);
  não se aplica a change feed nem a reads sem repetição.
- `spark.cosmos.preferredRegionsList`: colocar o cluster Spark na região do Cosmos e passar
  a região como preferred — reduz latência cross-region.
- `spark.cosmos.proactiveConnectionInitialization` (`DB1/Container1;DB2/Container2`) e
  `spark.cosmos.enforceNativeTransport` (netty nativo) para warm-up/transporte eficiente.

## Diagnóstico (`spark.cosmos.diagnostics`)

- `sampled` (recomendado): loga detalhe só de operações que violam thresholds — latência
  `pointOperationInMs` (default `1000`), `nonPointOperationInMs` (default `5000`) e
  `thresholds.requestCharge` (RU por operação); volume limitado por `sampling.maxCount`
  (default `100`) por `sampling.intervalInSeconds` (default `60`).
- `simple`/`feed`/`feed_details` aumentam muito o log (impacto de perf; `feed_details`
  inclui pk+id de itens — cuidado com dado sensível em log).
- `spark.cosmos.diagnostics.azureMonitor.*`: OpenTelemetry para Azure Monitor (sampling
  default `0.05`, métricas a cada `60s`) — base para evidenciar RU e latência reais.
- Evidência mínima antes de tunar: RU por operação (diagnostics/metrics), contagem de 429,
  partições Spark observadas no stage, e tamanho médio de documento.

## Fontes

- https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/integrated-cache (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/azure/cosmos-db/dedicated-gateway (retrieved: 2026-11-03)
