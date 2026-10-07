---
id: azure.eventhubs.kafka-and-spark
title: Event Hubs - tiers, partições, endpoint Kafka, Capture e Spark Structured Streaming
domain: azure-event-hubs
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-kafka-spark-tutorial
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-quotas
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-capture-overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.spark.streaming-state-checkpoint, azure.fabric.realtime-intelligence, azure.entra.managed-identity, azure.network.private-link-dns]
---

# Event Hubs — Kafka e Spark

## Tiers (quotas oficiais)

| | Basic | Standard | Premium | Dedicated |
|---|---|---|---|---|
| Mensagem | 256 KB | 1 MB | 1 MB | 20 MB |
| Consumer groups/hub | 1 | 20 | 100 | 1000 |
| Retenção | 1 dia | 7 dias | 90 dias | 90 dias |
| Partições/hub | 32 | 32 | 100 (200 por PU no namespace) | 1024 (2000 por CU) |
| Hubs/namespace | 10 | 10 | 100 por PU | 1000 |
| Escala | até 40 TU | até 40 TU | até 16 PU | 10 CU (mais via suporte) |
| Capture | não | cobrado à parte | incluído | incluído |
| Kafka | **não** | sim | sim | sim |

- TU: ingress 1 MB/s ou 1000 eventos/s; egress 2 MB/s ou 4096 eventos/s.
- 5 receptores non-epoch por consumer group; 12 authorization rules por namespace.
- Standard: 1000 consumer groups Kafka por namespace; 5000 conexões.
- Matriz célula a célula: `knowledge/matrices/eventhubs-tiers.yaml`.

## Endpoint Kafka

- `NAMESPACE.servicebus.windows.net:9093`; **SASL_SSL obrigatório**.
- Mecanismos: **OAUTHBEARER** (Entra ID + RBAC) ou **PLAIN** com
  `username="$ConnectionString"` e senha = connection string.
- Clientes Kafka ≥ 1.0. SAS tokens gerados **não** são suportados no endpoint Kafka.
- OAUTHBEARER em Java exige `sasl.login.callback.handler.class` customizado.
- **PREVIEW**: Kafka Streams e transações Kafka (Premium/Dedicated). Compressão gzip só em
  Premium/Dedicated.

## Spark Structured Streaming (conforme tutorial oficial)

```python
df = (spark.readStream.format("kafka")
  .option("subscribe", TOPIC)
  .option("kafka.bootstrap.servers", f"{NS}.servicebus.windows.net:9093")
  .option("kafka.sasl.mechanism", "PLAIN")
  .option("kafka.security.protocol", "SASL_SSL")
  .option("kafka.sasl.jaas.config", EH_SASL)       # connection string vinda de secret
  .option("kafka.request.timeout.ms", "60000")
  .option("kafka.session.timeout.ms", "30000")
  .option("kafka.group.id", GROUP)
  .option("failOnDataLoss", "true")
  .load())
```

- Sink Kafka: `topic` + `checkpointLocation`.
- Erro de gap de offsets: `spark.streaming.kafka.allowNonConsecutiveOffsets=true`.
- **Backpressure**: `maxOffsetsPerTrigger` limita registros por micro-batch.
- Checkpoint por query; replay limitado à **retenção** do tier.
- Databricks standard compute: opções `kafka.sasl.login.callback.handler.class`,
  `kafka.sasl.client.callback.handler.class`, `kafka.sasl.login.class` e
  `kafka.partition.assignment.strategy` **não suportadas** — OAUTHBEARER customizado
  exige outra abordagem ou dedicated compute.
- Fabric Runtime 1.3: `EventHubConnector` **deprecated** → usar conector Kafka.

## Capture

- Standard/Premium/Dedicated. Formato **Avro** (Parquet só via editor no-code do Stream
  Analytics). Destino Blob ou ADLS Gen2 (Gen1 aposentado); sem premium storage.
- Janela = primeiro entre tempo e tamanho; grava arquivos **vazios** quando ocioso.
- Caminho: `{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}`.
- Não consome quota de egress; exige permissão de escrita (Storage Blob Data Owner).

## Rede

- Private DNS zone: `privatelink.servicebus.windows.net`.

## O que NÃO afirmar

- Exactly-once com sink Kafka (Spark documenta at-least-once).

## Não verificado

- Classe JAAS shaded do Databricks (`kafkashaded...`) e config OAUTHBEARER Entra em Spark.

## Fontes

- https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-kafka-spark-tutorial (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-quotas (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-capture-overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3 (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations (retrieved: 2026-10-06)
