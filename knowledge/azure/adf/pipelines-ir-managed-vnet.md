---
id: azure.adf.pipelines-ir-managed-vnet
title: Azure Data Factory - pipelines, IR, managed VNet, triggers e monitoramento
domain: azure-data-factory
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipeline-execution-triggers
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.fabric.data-factory, azure.synapse.pipelines-and-linked-services, azure.network.private-link-dns, azure.keyvault.secrets-and-rbac, azure.databricks.workflows]
---

# Azure Data Factory — pipelines, IR e managed VNet

## Modelo

- **Pipeline** = grupo de **atividades** (movimento: Copy; transformação: Data Flow,
  Databricks notebook/Python/JAR, stored procedure…; controle: ForEach, If, Until,
  Execute Pipeline, Lookup, Get Metadata, Wait, Web).
- **Linked service** = conexão + autenticação; **dataset** = estrutura/caminho sobre um
  linked service; **parâmetros** de pipeline/dataset/linked service e expressões `@{...}`
  (ex.: `@pipeline().parameters.x`, `@trigger().scheduledTime`).
- Execução: manual (on-demand, REST/SDK/PowerShell) ou por trigger; cada run tem GUID.

## Integration runtimes

| IR | Onde roda | Uso |
|---|---|---|
| Azure (auto-resolve ou regional) | gerenciado | cloud-to-cloud, data flows |
| Self-hosted (SHIR) | VM/host do cliente (até 8 nós) | on-prem / rede privada; Key Vault suportado |
| Azure-SSIS | gerenciado | pacotes SSIS |

## Managed VNet e managed private endpoints

- Azure IR dentro da **managed VNet** do ADF usa private endpoints para data stores;
  só na mesma região do factory. Um IR global existente **não** pode virar managed VNet
  (nem o contrário).
- **Managed private endpoint** nasce **Pending**; o dono do recurso alvo aprova. Só
  endpoints **Approved** trafegam.
- Custom DNS **não** é suportado na managed VNet. Saída pública: todas as portas abertas.
- Requer o resource provider `Microsoft.Network` registrado.
- Serviços com private endpoint nativo citados: Azure Databricks, Functions (Premium),
  Key Vault, Azure ML, Private Link Service, Microsoft Purview.
- Limitação: um recurso PaaS com private endpoint vindo de **outra** VNet deixa de ser
  acessível pela rede pública a partir da managed VNet.
- Linked service de Key Vault não referencia IR: o PE para Key Vault é criado a partir de
  um linked service de data store que referencia o IR com managed VNet; "test connection"
  do KV só valida formato de URL.

## TTL e cold start

- Na managed VNet, cada Copy sobe compute novo: **cold start de alguns minutos**.
- TTL (Copy, pipeline e external compute) mantém compute quente; reservado define cobrança
  (o output deixa de trazer `billingReference`). TTL de pipeline/external **não** pode ser
  desligado. Não existe TTL no auto-resolve IR default.
- 2 DIU **não** é suportado para Copy em managed VNet; DIU do TTL não autoescala.
- Interactive authoring: TTL default 60 min.
- Capacidade por nó: ~50 atividades de pipeline (≈4 para Script/Lookup com Always
  Encrypted); ~800 atividades externas.

## Triggers

| | Schedule | Tumbling window |
|---|---|---|
| Backfill | não | sim |
| Retry | não | sim (default 0; auto-retry em 400/429/500) |
| Concorrência | não | 1–50 |
| Relação | many-to-many | 1:1 |
| Estado | fire-and-forget | espera o run terminar |

- Storage event e custom event (Event Grid). Parar/reiniciar trigger de evento retoma o
  padrão antigo: recriar para começar sem histórico.
- Fuso com horário de verão ajusta só para recorrência ≥ dias.

## Monitoramento

- Monitor do ADF (runs de pipeline/atividade/trigger) + **diagnostic settings** do Azure
  Monitor para Log Analytics (até 5 settings por recurso; um de cada tipo de destino por
  setting).

## Rede/DNS

- Zonas: `privatelink.datafactory.azure.net` (dataFactory) e `privatelink.adf.azure.com`
  (portal).

## Fatos que o Forge extrai

- Linked service com segredo inline; Copy em loop sequencial em managed VNet sem TTL
  (cold start repetido); schedule trigger onde é preciso backfill.

## Não verificado

- Lista de atividades e sintaxe de expressões além de `@trigger().scheduledTime`/
  `@trigger().startTime` (página de atividades/expressões não relida).

## Fontes

- https://learn.microsoft.com/en-us/azure/data-factory/concepts-integration-runtime (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipeline-execution-triggers (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings (retrieved: 2026-10-06)
