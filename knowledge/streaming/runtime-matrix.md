---
id: spark.streaming.runtime-matrix
title: Matriz de versões streaming — upstream Apache vs runtime efetivo gerenciado no Azure
domain: spark-streaming
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/
    retrieved: 2026-10-02
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3
    retrieved: 2026-10-02
  - url: https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-34-runtime
    retrieved: 2026-10-02
  - url: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
    retrieved: 2026-10-02
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-for-kafka-ecosystem-overview
    retrieved: 2026-10-02
verified_at: 2026-10-02
versions: {dbr_streaming: ["16.4 LTS", "17.0"], fabric_runtime: ["1.3"], synapse_spark: ["3.4"]}
status: VERIFIED
preview: false
related: [azure.eventhubs.kafka-and-spark, azure.databricks.runtime-and-compute, azure.synapse.spark-runtimes, azure.spark.streaming-state-checkpoint]
---

# Matriz de versões streaming (Azure)

Data da revalidação: 2026-10-02.

Esta matriz separa, por plataforma, a versão **upstream** do Apache Spark/Structured
Streaming do **runtime efetivo** que o serviço gerenciado executa. As duas colunas
existem porque afirmar a upstream como se fosse a gerenciada já produziu recomendação
errada: o upstream define a API disponível; o runtime efetivo define o que de fato roda,
com backports e restrições do fornecedor.

## Estados possíveis por célula

- `VERIFIED` — a versão vem da página oficial listada em Fontes, lida na data da
  revalidação.
- `UNRESOLVED` — a plataforma existe mas a página oficial não publica a versão do
  componente; nunca preencher com a upstream "porque provavelmente é a mesma".
- `N/A + motivo` — a célula não se aplica, com a razão escrita (ex.: componente que
  não existe naquele serviço).
- `PREVIEW` — versão em preview público; toda célula preview carrega a marca.

## Matriz

| Plataforma | Componente | Upstream | Runtime efetivo | Estado |
|---|---|---|---|---|
| Azure Databricks | Structured Streaming (DBR 16.4 LTS) | Spark 3.5.x | DBR 16.4 LTS (Spark 3.5, Photon opcional) | `VERIFIED` |
| Azure Databricks | Delta Live Tables / Pipelines | — | Canal `current`/`preview` do runtime | `VERIFIED` |
| Microsoft Fabric | Structured Streaming (Runtime 1.3) | Spark 3.5.x | Fabric Runtime 1.3 (Spark 3.5, Delta 3.2) | `VERIFIED` |
| Microsoft Fabric | Eventstream / Real-Time Intelligence | `N/A + motivo: não é Spark` | Eventstream gerenciado | `VERIFIED` |
| Azure Synapse | Structured Streaming (Spark pool 3.4) | Spark 3.4.x | Synapse Runtime for Apache Spark 3.4 | `VERIFIED` |
| Azure Synapse | Spark pool 3.5 | `UNRESOLVED` | `UNRESOLVED` | `UNRESOLVED` |
| Event Hubs | Endpoint Kafka (protocolo) | Kafka protocol ≥ 1.0 | Gerenciado; não expõe versão de broker | `VERIFIED` |
| HDInsight/AKS Spark | Structured Streaming | `UNRESOLVED` | `UNRESOLVED` | `UNRESOLVED` |

## Divergências conhecidas

A coluna **Divergência** registra onde o runtime efetivo difere da upstream de forma
que muda recomendação:

| Plataforma | Divergência | Impacto prático |
|---|---|---|
| Databricks | Photon não executa operadores de streaming stateful em todas as versões | `stateStore` e `flatMapGroupsWithState` caem para execução JVM; medir antes de afirmar ganho |
| Databricks | RocksDB state store é gerenciado por DBR, não pela conf upstream | `spark.sql.streaming.stateStore.providerClass` aceita `rocksdb` sem jar extra |
| Fabric Runtime 1.3 | Default Delta Lake 3.2; `delta.enableChangeDataFeed` em streaming exige conf explícita | checkpoint em OneLake usa `abfss://`, não `s3a://` |
| Synapse 3.4 | Sem `rocksdb` provider da distribuição | state store default HDFS-backed; latência de checkpoint maior em estado grande |
| Event Hubs | `maxOffsetsPerTrigger` é limite de throughput do namespace, não de Kafka | estourar o limite vira `ReceiverDisconnected`, não rebalancing |

## Limites da evidência local

Esta matriz é leitura de páginas oficiais, não medida em cluster. Dois limites
permanecem por contrato:

1. A versão patch-level efetiva do runtime (`16.4.x` exato) só é observada no
   cluster — `spark.version` no driver, ou `runtime_version` em `clusters/get`.
2. Suporte a API nova do upstream (ex.: `transformWithState`) depende do runtime
   efetivo, não do número do upstream declarado; sem VERIFIED explícito, tratar
   como UNRESOLVED.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3
- https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-34-runtime
- https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-for-kafka-ecosystem-overview
