---
id: azure.databricks.workflows
title: Lakeflow Jobs (Workflows) e pipelines declarativos no Azure Databricks
domain: azure-databricks
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/jobs/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/ldp/expectations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipeline-execution-triggers
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.databricks.runtime-and-compute, azure.adf.pipelines-ir-managed-vnet, data-quality.contracts-and-expectations, azure.observability.monitor-log-analytics]
---

# Lakeflow Jobs (Workflows) no Azure Databricks

## Resumo

"Lakeflow Jobs" é o nome atual da orquestração nativa do Databricks (antes "Workflows").
Um **job** coordena **tasks** em DAG, com **triggers**, parâmetros, notificações e Git.
Pipelines declarativos (Lakeflow pipelines, antigo DLT) são um tipo de task.

## Conceitos

| Conceito | O que é |
|---|---|
| Job | recurso principal; DAG de tasks; trigger, parâmetros, notificações, Git |
| Task | unidade de trabalho: notebook, pipeline, Python script, JAR, SQL, dbt, if/else, for each, … |
| Trigger | por tempo (agenda) ou por evento (ex.: chegada de arquivo em storage) |
| Control flow | branching (if/else) e looping (for each) |

## Limites documentados

- **2000** task runs concorrentes por workspace (excesso → `429 Too Many Requests`).
- **10000** jobs criados por hora por workspace (inclui "runs submit").
- **12000** jobs salvos por workspace.
- **1000** tasks por job.
- Parâmetros de job limitados a **10.000** caracteres quando tasks usam valores dinâmicos.

## Gestão programática

Databricks CLI, **Declarative Automation Bundles** (nome atual na página; antes conhecido
como Databricks Asset Bundles), extensão VS Code, SDKs e Jobs REST API. Orquestração
externa: Azure Data Factory (atividades Databricks notebook/Python/JAR) e Apache Airflow.

## Observabilidade

- UI de runs por task; notificações por e-mail, Slack, webhooks.
- System tables: `system.lakeflow.jobs`, `system.lakeflow.job_tasks`,
  `system.lakeflow.job_run_timeline`, `system.lakeflow.job_task_run_timeline` (GA);
  `system.lakeflow.pipelines` e `pipeline_update_timeline` (**Public Preview**);
  pipeline events (**Beta**).

## Pipelines declarativos e expectations

- Expectations: `CONSTRAINT nome EXPECT (expr)` com ação **warn** (default),
  `ON VIOLATION DROP ROW`, `ON VIOLATION FAIL UPDATE`; Python `@dp.expect`,
  `expect_or_drop`, `expect_or_fail`, `expect_all*`. Ver
  `data-quality.contracts-and-expectations`.

## ADF orquestrando Databricks vs Lakeflow Jobs

| Critério | Lakeflow Jobs | ADF → Databricks |
|---|---|---|
| Lineage UC/Purview | runs de notebook entram no lineage | Purview **não mostra** lineage Databricks disparado por ADF |
| Compute | job compute/serverless | job cluster criado pela atividade |
| Retry/backfill | retries por task, repair run | tumbling window trigger com retry e backfill |

## Fatos que o Forge extrai

- Job com all-purpose cluster em vez de job compute (custo).
- Task sem retry/timeout; job sem notificação de falha.
- Jobs com `existing_cluster_id` compartilhado entre muitos jobs (contenção).

## Não verificado

- Nomes exatos dos campos de retry/timeout na Jobs API e a lista completa de task types
  (página de configuração de tasks não relida).

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/jobs/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/ldp/expectations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/concepts-pipeline-execution-triggers (retrieved: 2026-10-06)
