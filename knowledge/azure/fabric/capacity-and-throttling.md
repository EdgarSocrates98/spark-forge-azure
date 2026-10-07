---
id: azure.fabric.capacity-and-throttling
title: Fabric capacity - F SKUs, CU, smoothing, bursting e estágios de throttling
domain: azure-finops
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/enterprise/licenses
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/enterprise/throttling
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.finops.cost-management-and-dbu, azure.fabric.data-engineering-spark, azure.fabric.realtime-intelligence, azure.observability.monitor-log-analytics]
---

# Fabric capacity e throttling

## SKUs e CU

| SKU | CU | Nota |
|---|---|---|
| F2, F4, F8, F16, F32 | 2, 4, 8, 16, 32 | < F64: viewers precisam de Pro/PPU para Power BI |
| F64 | 64 | = P1/A4 (8 vCores); viewers com licença Free consomem Power BI |
| Trial | 64 | |
| F128 … F8192 | = número | |

- F é cobrado **por segundo** (mínimo 1 minuto); reserva anual opcional; SKUs P em
  aposentadoria. Matriz: `knowledge/matrices/fabric-capacity-throttling.yaml`.

## Timepoints, smoothing e bursting

- Timepoint = **30 s** (2.880 por 24 h).
- Operações **interativas**: suavizadas em ≥ 5 min, até 64 min.
- Operações de **background**: suavizadas em **24 h** (Spark, pipelines, warehouse…;
  warehouse é background).
- **Bursting** permite uso temporário acima da capacidade; o excedente vira "future
  capacity" a ser pago (carryforward/burndown).

## Estágios de throttling (por capacidade futura consumida)

| Overage acumulado | Efeito |
|---|---|
| ≤ 10 min | overage protection (sem throttling) |
| 10–60 min | **interativo atrasado** (+20 s) |
| 60 min – 24 h | **interativo rejeitado** |
| > 24 h | **background rejeitado** (tudo rejeitado) |

- Operações em andamento não são interrompidas. Erro de rejeição: `CapacityLimitExceeded`.
- Real-Time Intelligence pula o estágio de atraso de 20 s e rejeita só com 60 min.
- Eventstreams reduzem alocação de CU em vez de rejeitar.

## Recuperação

- Escalar o SKU; pausar/retomar a capacidade; **capacity overage billing** (taxa 3x);
  esperar o burndown do carryforward. (Efeito exato de pause/resume sobre a cobrança do
  carryforward não foi detalhado aqui — consultar a página de throttling.)
- **Autoscale Billing for Spark**: Spark sai do modelo de bursting/smoothing da capacidade.

## Capacity Metrics app

- Instalada pelo capacity admin. Páginas: Health, Compute (14 dias), Storage (30 dias),
  Timepoint (+summary/item detail), Autoscale for Spark, Plan capacity.
- Latência de 10–15 min; **sem alertas** nativos (usar eventos de capacidade + Activator).

## Fatos e regras do Forge

- Capacidade com % de rejeição interativa > 0 em janela: achado de saturação, com
  evidência por timepoint.
- Jobs Spark grandes em capacidade pequena sem Autoscale Billing: risco de throttling de
  background após 24 h de overage.
- **Não** estimar economia de troca de SKU: só apresentar consumo observado vs capacidade.

## Não verificado

- Preço por CU/hora por região (fora do escopo; consultar calculadora oficial).

## Fontes

- https://learn.microsoft.com/en-us/fabric/enterprise/licenses (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/enterprise/throttling (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview (retrieved: 2026-10-06)
