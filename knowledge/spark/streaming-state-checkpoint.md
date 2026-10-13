---
id: azure.spark.streaming-state-checkpoint
title: Structured Streaming - estado, watermark, checkpoint, offsets e garantias
domain: spark-streaming
authority: apache_official
sources:
  - url: https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-kafka-spark-tutorial
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/photon
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {spark: ["4.2.0"]}
status: VERIFIED
preview: false
related: [azure.eventhubs.kafka-and-spark, lakehouse.delta-lake, azure.spark.execution-model]
---

# Structured Streaming — estado, watermark, checkpoint, offsets e garantias

## Resumo

Structured Streaming trata o stream como tabela que cresce e executa micro-batches. A
recuperação depende de **checkpoint** (offsets + estado) em storage compatível com HDFS
(no Azure: ABFSS/ADLS ou volume UC). Garantia fim-a-fim depende de **fonte reexecutável**
+ **sink idempotente**: não é propriedade do Spark sozinho.

## Garantias — o que a doc diz (e o que não diz)

- Requisitos: fonte reexecutável (File, Kafka, Rate com offsets) e sink idempotente.
- **File sink**: exactly-once segundo a doc. **Kafka sink: at-least-once.** Outros sinks:
  dependem da implementação.
- `foreachBatch`: idempotência é responsabilidade do código (dedupe por `batchId`,
  `MERGE` determinístico).
- Event Hubs (via endpoint Kafka) como fonte é reexecutável dentro da retenção do hub;
  perdeu a retenção, perdeu o replay.

**Regra do Forge:** nunca declarar "exactly-once" sem evidência de sink idempotente e
checkpoint estável. O máximo que se afirma por padrão é "at-least-once com dedupe
recomendado".

## Checkpoint

- `.option("checkpointLocation", path)` é obrigatório para tolerância a falha.
- Um checkpoint por query; **nunca** compartilhar entre queries.
- Mudar a query (agregação, chaves, operadores com estado) pode invalidar o checkpoint;
  mudanças compatíveis são restritas.
- Apagar checkpoint = recomeçar dos offsets iniciais configurados (risco de duplicar ou pular).
- Em Databricks standard access mode, `sourceArchiveDir` de `cleanSource=archive` precisa
  estar na mesma external location da fonte (UC).

## Watermark e estado

- `withWatermark("eventTime", "10 minutes")`: o motor **garante não descartar** dados com
  atraso menor que o limiar; dados mais atrasados **podem ou não** ser processados
  (descartar não é garantido).
- Watermark é necessário para limpar estado em agregações e joins stream-stream
  (opcional em inner join, mas sem ele o estado cresce).
- Output modes: **append** (default; agregação exige watermark), **update**, **complete**
  (sem limpeza de estado).
- Estado sem limite cresce até OOM ou checkpoint lento: fato a observar (tamanho de state
  store por micro-batch).

## Triggers

| Trigger | Uso |
|---|---|
| default | próximo micro-batch quando o anterior termina |
| `processingTime='5 seconds'` | intervalo fixo |
| `availableNow=True` | processa o disponível e para (substitui `once`) |
| `once` | **deprecated** |

## Offsets e backpressure (Kafka / Event Hubs)

- `maxOffsetsPerTrigger` limita registros por micro-batch (controle de taxa).
- `failOnDataLoss`: com `false`, offsets expirados são pulados silenciosamente — perda
  de dado mascarada. O default `true` é do guia de integração Kafka do Spark, que não foi
  relido nesta verificação (UNVERIFIED).
- Gap de offsets no Event Hubs: o tutorial oficial indica
  `spark.streaming.kafka.allowNonConsecutiveOffsets=true`.

## Plataforma

- Photon acelera apenas streaming **stateless**.
- Databricks standard compute: sem socket source; opções Kafka
  `kafka.sasl.login.callback.handler.class` e afins não suportadas; `foreachBatch` Python
  não suporta multithread.
- System tables como fonte de stream: usar `skipChangeCommits=true`; VACUUM de 7 dias
  quebra streams atrasados > 7 dias.

## Fatos que o Forge extrai

- `writeStream` sem `checkpointLocation`; mesmo checkpoint em duas queries.
- agregação com estado sem `withWatermark`; `outputMode("complete")` em stream longo.
- `failOnDataLoss=false`; `trigger(once=True)` (deprecated).
- `foreachBatch` sem chave de idempotência.

## Fontes

- https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-kafka-spark-tutorial (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/photon (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ (retrieved: 2026-10-06)
