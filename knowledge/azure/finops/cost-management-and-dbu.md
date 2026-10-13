---
id: azure.finops.cost-management-and-dbu
title: FinOps Azure - Cost Management APIs, Databricks billing e economia de capacidade Fabric
domain: azure-finops
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/manage-automation
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/rest/api/cost-management/budgets/create-or-update?view=rest-cost-management-2025-03-01
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/enterprise/licenses
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/photon
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {cost_management_api: ["2025-03-01"]}
status: VERIFIED
preview: false
related: [azure.fabric.capacity-and-throttling, azure.databricks.runtime-and-compute, azure.observability.monitor-log-analytics, agentic.evidence-first]
---

# FinOps Azure para dados

## Regra do produto

O Forge **nunca promete economia** ("X% mais barato"). Ele correlaciona custo observado ×
compute × duração × configuração e mostra o que mudaria; estimativa só com baseline
medido e rotulada como estimativa. Desconhecido ≠ zero.

## Cost Management APIs

| API | Uso | Limites/observações |
|---|---|---|
| **Cost Details** (`generateCostDetailsReport`, api-version 2025-03-01) | detalhe de custo por linha | assíncrona: POST → poll → `blobLink` CSV; escopos **EA/MCA** apenas; ≤ 1 chamada/dia por escopo (dados atualizam a cada 4 h); fatiar por dia/semana; > 2 GB/mês → usar Exports |
| **Exports** | export agendado para storage | recomendada para volume |
| **Query** | agregações ad hoc | QPU: 12/10 s, 60/min, 600/h por tenant; headers `x-ms-ratelimit-microsoft.costmanagement-qpu-{consumed,remaining,retry-after}`; 429 |
| **Budgets** (`Microsoft.CostManagement/budgets`, 2025-03-01) | alertas | escopos subscription / EA billing account / MCA billing profile / CSP customer; até 5 thresholds Actual + 5 Forecasted; avaliação **diária**; GET mostra último gasto avaliado (usar Query para "agora") |

## Databricks: `system.billing.usage`

- Disponibilidade ~**12 h** de atraso; tabela **global**; retenção 365 dias.
- Colunas: `record_id`, `account_id`, `workspace_id`, `sku_name`, `cloud`,
  `usage_start_time`, `usage_end_time`, `usage_date`, `custom_tags`, `usage_unit`,
  `usage_quantity`, `usage_metadata`, `identity_metadata`, `record_type`,
  `ingestion_date`, `billing_origin_product`, `product_features` (`is_photon`,
  `is_serverless`, …), `usage_type`.
- `record_type` ∈ ORIGINAL / RETRACTION / RESTATEMENT: **somar** para obter o líquido.
- No Azure, `usage_metadata.metastore_id` é sempre nulo.
- Preço: `system.billing.list_prices` (histórico de preço de SKU; schema não relido).
- Photon tem taxa de DBU diferente (multiplicador não verificado).
- DBU é só parte do custo: VMs (compute clássico), storage e rede vêm na fatura Azure
  (Cost Management) — correlacionar por tags/ids, não somar às cegas.

## Fabric

- Capacidade F cobrada por segundo (mín. 1 min) enquanto ativa; reserva anual opcional.
- Overage billing a 3x; Autoscale Billing for Spark separa Spark do smoothing.
- Recurso ocioso: capacidade ligada sem consumo → evidência para pausar (ação humana).

## Recursos ociosos (sinais, não veredito)

- All-purpose cluster sem autoterminação; SQL warehouse sem auto stop.
- Capacidade Fabric ativa com CU% ~0 em janela longa.
- Event Hubs Premium/Dedicated subutilizado; Capture gravando arquivos vazios.
- Storage com arquivos pequenos em excesso (custo de transação em incrementos de 4 MB).

## Saída esperada de um achado de custo

```yaml
observed: {source: system.billing.usage, window: 2026-09-01..2026-09-30, dbus: 1234.5}
estimated: null            # sem baseline -> null, nunca 0
unknown: [vm_cost_from_cost_management]
recommendation: "habilitar autoterminação de 30 min (decisão humana)"
```

## Fontes

- https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/manage-automation (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/rest/api/cost-management/budgets/create-or-update?view=rest-cost-management-2025-03-01 (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/enterprise/licenses (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/photon (retrieved: 2026-10-06)
