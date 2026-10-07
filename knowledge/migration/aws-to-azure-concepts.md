---
id: migration.aws-to-azure-concepts
title: Conceitos AWS para Azure em dados - mapeamento NÃO 1:1 (DEFER)
domain: migration
authority: internal
roadmap: DEFER
sources:
  - url: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.adls.gen2, azure.fabric.onelake-shortcuts, azure.eventhubs.kafka-and-spark, azure.unity-catalog.securable-model, governance.multi-layer-conflicts, lakehouse.iceberg]
---

# Conceitos AWS → Azure (dados)

> **Status de roadmap: DEFER / futuro.** Migração AWS → Azure está fora do MVP v0.1.0
> (Product Definition). Este documento existe para impedir mapeamentos ingênuos, não para
> guiar migração. O Forge não gera plano de migração a partir dele.

## Regra central

Os serviços **não são equivalentes 1:1**. Cada linha abaixo é "ponto de partida para
análise", com as diferenças que quebram a analogia.

| AWS | Candidatos Azure | Onde a analogia quebra |
|---|---|---|
| S3 | ADLS Gen2; OneLake | ADLS exige HNS para UC; autorização = RBAC → ABAC → ACL (ACL não restringe RBAC); OneLake é SaaS por workspace/item com shortcuts (inclusive **para** S3) |
| Glue (ETL) | ADF; Fabric Data Factory; Databricks Jobs | ADF é PaaS com IR; Fabric DF é SaaS sem IR (gateways); Databricks é Spark gerenciado — três modelos de custo e rede diferentes |
| Glue Data Catalog | Unity Catalog; OneLake catalog; Purview Data Map | UC aplica acesso; Purview cataloga/classifica e **não** concede SELECT; **não existe "Glue" no Azure** para catálogo Iceberg |
| EMR | Azure Databricks; Fabric Spark; Synapse Spark | Synapse sem Spark 4.x; Fabric cobra por capacidade F (CU, smoothing, throttling); Databricks por DBU + VM |
| Kinesis Data Streams | Event Hubs; Fabric Eventstreams | modelo de partição/retenção por tier; Eventstreams at-least-once, 1 MB, 90 dias |
| MSK | Event Hubs (endpoint Kafka 9093) | SASL_SSL obrigatório; sem Kafka no Basic; Kafka Streams/transações em PREVIEW; não é cluster Kafka gerenciado |
| Lake Formation | Unity Catalog + Purview + Azure RBAC + ADLS ACL | não há serviço único: permissões ficam distribuídas em camadas independentes (ver `governance.multi-layer-conflicts`) |
| IAM roles | Entra ID managed identities / service principals + Azure RBAC | control plane × data plane são roles distintas; workload identity federation |

## Armadilhas que o Forge sinaliza (quando for implementado)

- Código com `glue` como tipo de catálogo Iceberg ou `s3a://` paths em projeto Azure.
- Política "estilo Lake Formation" reimplementada só em ACL ADLS com roles amplas
  (RBAC vence ACL).
- Expectativa de exactly-once herdada de configurações Kinesis/MSK sem evidência.

## Por que DEFER

- Escopo v0.1.0 é Azure-first; capacidades multi-cloud ficam para depois (Product
  Definition, não-objetivos).
- Mapeamento confiável exige fontes AWS verificadas, fora desta base.

## Fontes

- https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects (retrieved: 2026-10-06)
