---
id: azure.observability.monitor-log-analytics
title: Observabilidade de dados - Azure Monitor, Log Analytics, event logs, system tables e Fabric
domain: azure-observability
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/account-settings/audit-log-delivery
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.databricks.runtime-and-compute, azure.fabric.capacity-and-throttling, azure.finops.cost-management-and-dbu, azure.spark.execution-model, agentic.evidence-first]
---

# Observabilidade de dados no Azure

> Escopo: observabilidade das **cargas de dados do cliente**. AgentOps (telemetria do
> próprio Forge/agentes, OTel, receipts) é outro assunto e não está aqui.

## Azure Monitor e diagnostic settings

- Fontes: **platform metrics** e **activity log** (coletados automaticamente) e
  **resource logs** (só com diagnostic setting).
- Destinos: **Log Analytics workspace**, **Storage account**, **Event Hubs**, soluções de
  parceiros.
- Regras: destino precisa existir antes; para recurso regional, storage/Event Hubs na
  **mesma região**; com firewall, liberar "trusted Microsoft services"; **até 5**
  diagnostic settings por recurso; um destino de cada tipo por setting; Premium storage
  não é destino; Event Hub compactado não é destino.
- Category groups: `allLogs` e `audit`.
- Latência: dados começam a fluir em até **90 min** após criar o setting.
- Custo: coletar só categorias necessárias; transformações filtram na ingestão.
- Apagar/renomear recurso: apagar o diagnostic setting (pode ser reaplicado a recurso
  recriado com mesmo nome).
- Private Link (AMPLS): zonas `privatelink.monitor.azure.com`, `privatelink.oms.opinsights.azure.com`,
  `privatelink.ods.opinsights.azure.com`, `privatelink.agentsvc.azure-automation.net`.

## Azure Databricks

- **Diagnostic logs** via diagnostic settings: exigem **Premium**; tipicamente < 15 min,
  **sem garantia**; `requestParams` truncado acima de 100 KB; ações automáticas aparecem
  como `System-User`.
- A Databricks **recomenda `system.access.audit`** (Public Preview) e desencoraja exportar
  audit para fora da plataforma.
- System tables úteis: `system.compute.clusters`, `system.compute.node_timeline` (90 d,
  utilização), `system.compute.warehouse_events`, `system.query.history`,
  `system.lakeflow.job_run_timeline`, `system.billing.usage`. Não são tempo real.
- **Spark event log**: entregue por cluster log delivery em compute clássico; é a fonte
  de métricas por stage/task para o Forge. Serverless não entrega event log.

## Fabric

- **Capacity Metrics app**: Compute 14 d, Storage 30 d, Timepoint; latência 10–15 min;
  sem alertas.
- **Monitor hub**: job runs, alertas, capacidade e custo, agentes — **em preview** na
  página lida.
- Spark: histórico de aplicações por notebook/SJD (Spark UI/monitoring); não relido aqui.

## Synapse / ADF

- Monitor nativo + diagnostic settings para Log Analytics (pipeline/activity/trigger runs).

## Princípios do Forge

- Evidência observada (logs, system tables) ≠ estimativa; ausência de log ≠ ausência de
  evento (latência e retenção existem).
- Toda leitura é read-only e opt-in; nada de habilitar diagnostic settings sem
  autorização.

## Não verificado

- Nomes de tabelas Log Analytics resource-specific para Databricks/ADF.
- Workspace monitoring (Eventhouse) do Fabric.

## Fontes

- https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/account-settings/audit-log-delivery (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
