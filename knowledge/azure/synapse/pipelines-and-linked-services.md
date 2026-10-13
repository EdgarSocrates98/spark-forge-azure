---
id: azure.synapse.pipelines-and-linked-services
title: Synapse pipelines e linked services - diferenças para ADF
domain: azure-synapse
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/synapse-analytics/data-integration/concepts-data-factory-differences
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipeline-execution-triggers
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.adf.pipelines-ir-managed-vnet, azure.synapse.spark-runtimes, migration.synapse-to-fabric, azure.fabric.data-factory]
---

# Synapse pipelines e linked services

## Resumo

Synapse pipelines e data flows são baseados no motor do ADF: mesmos conceitos de pipeline,
atividade, dataset, linked service, trigger e integration runtime. As diferenças estão em
IR, algumas atividades e deployment.

## Diferenças documentadas (Synapse × ADF)

| Recurso | ADF | Synapse |
|---|---|---|
| IR cross-region (Data Flows) | sim | **não** |
| Compartilhar IR entre factories | sim | **não** |
| Power Query activity | sim | **não** |
| Global parameters | sim | **não** |
| Templates | Template Gallery | Knowledge center |
| Git | sim | sim |
| Monitorar Spark de Data Flow | não | sim (Spark pools Synapse) |
| Deploy de pipelines/flows por ARM template | sim | **não** |

- Tipos de IR em Synapse pipelines: **Azure** e **self-hosted** apenas (sem Azure-SSIS).

## Linked services e datasets

- Linked service = string de conexão + autenticação (MI do workspace, service principal,
  chave, Key Vault). Dataset = forma/localização dos dados sobre um linked service.
- No Fabric esses dois viram **connection** (ver `azure.fabric.data-factory`).

## Triggers (mesmo modelo do ADF)

- Schedule (wall-clock, many-to-many com pipelines), tumbling window (estado, backfill,
  retry, concorrência 1–50, relação 1:1), storage event e custom event (Event Grid).
- Parar e reiniciar trigger de evento retoma o padrão antigo — recriar o trigger para
  começar sem histórico.

## Rede

- Private endpoints de workspace Synapse: zonas `privatelink.sql.azuresynapse.net`
  (Sql/SqlOnDemand), `privatelink.dev.azuresynapse.net` (Dev),
  `privatelink.azuresynapse.net` (Studio via private link hub).

## Migração

- Pipelines Synapse → Fabric Data Factory: guia oficial de upgrade (URL conhecida,
  conteúdo não lido). Atividades Synapse notebook/SJD **não existem** no Fabric.

## Fatos que o Forge extrai

- Linked services com chave/connection string inline (sem Key Vault/MI).
- Uso de global parameters em código que se pretende portar para Synapse (não suportado).
- Atividades Synapse notebook/SJD em pipelines candidatos a Fabric (bloqueio).

## Não verificado

- Detalhes de autenticação por linked service em Synapse (por conector).

## Fontes

- https://learn.microsoft.com/en-us/azure/synapse-analytics/data-integration/concepts-data-factory-differences (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipeline-execution-triggers (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
