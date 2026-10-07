---
id: azure.fabric.realtime-intelligence
title: Fabric Real-Time Intelligence - Eventstreams, Eventhouse e Activator
domain: fabric-realtime
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/enterprise/throttling
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.eventhubs.kafka-and-spark, azure.fabric.capacity-and-throttling, azure.spark.streaming-state-checkpoint, azure.fabric.onelake-shortcuts]
---

# Fabric Real-Time Intelligence (RTI)

## Componentes

Real-Time hub, **Eventstreams**, **Eventhouse** (KQL databases; consulta em KQL e T-SQL),
Real-Time dashboards, **Activator**, Map, data agents, digital twin builder (**PREVIEW**).

## Eventstreams

- Fontes: Event Hubs, IoT Hub, bancos via CDC, Kafka, Confluent, Amazon MSK, Kinesis,
  Google Pub/Sub, MQTT, entre outras.
- Destinos: Eventhouse, Lakehouse (Delta), custom endpoint, derived stream, Activator,
  Spark Notebook (**PREVIEW**).
- Endpoint Kafka do Eventstream é sustentado por um **namespace Event Hubs criado
  automaticamente**.
- Limites: mensagem de **1 MB**, retenção de **90 dias**, entrega **at-least-once**;
  exige capacidade **≥ F4**.
- **PREVIEW**: schema-aware eventstream, operador SQL, DeltaFlow CDC, fontes HTTP/MQTT/
  Oracle CDC/ADX/Mirrored DB, workspace private link, capacity operation events.
  Event schema sets do Schema Registry: GA.

## Eventhouse

- Bancos KQL; detecção de anomalia nativa; disponibilidade no OneLake.
- Rótulo GA explícito **não** encontrado na página: tratar como GA com status do rótulo
  UNVERIFIED.
- Shortcuts em KQL DB viram external tables (`external_table('X')`).

## Activator

- Motor de regras no-code. Fontes: eventstreams, eventos Fabric/Azure, Power BI,
  Real-Time dashboards.
- Ações: pipelines, notebooks, Spark jobs, dataflows, UDFs, copy jobs, Power Automate,
  Teams, e-mail.
- **PREVIEW**: publicação de business events, regras sobre warehouse SQL, regras de ontologia.

## Capacidade

- RTI **não** tem o estágio de atraso de 20 s: rejeita apenas com 60 min de capacidade
  futura consumida.
- Eventstreams reduzem alocação de CU em vez de rejeitar.

## Event Hubs vs Eventstreams (decisão)

| Critério | Event Hubs | Eventstream |
|---|---|---|
| Modelo | PaaS, TU/PU/CU | SaaS na capacidade F |
| Retenção máx | 90 dias (Premium/Dedicated) | 90 dias |
| Mensagem | até 1 MB (20 MB Dedicated) | 1 MB |
| Garantia | depende do consumidor | at-least-once |
| Spark | conector Kafka (`azure.eventhubs.kafka-and-spark`) | destino Notebook em preview |

## O que NÃO afirmar

- Exactly-once em Eventstream (doc diz at-least-once).
- Que Eventhouse substitui Event Hubs para ingestão Kafka de alta escala sem medição.

## Não verificado

- Rótulo GA do Eventhouse.

## Fontes

- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/enterprise/throttling (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts (retrieved: 2026-10-06)
