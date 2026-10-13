---
id: azure.databricks.runtime-and-compute
title: Azure Databricks - runtimes LTS, Photon, serverless, compute, access modes, secrets e system tables
domain: azure-databricks
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/18
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/photon
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/environment-version/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/security/secrets/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/account-settings/audit-log-delivery
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {dbr: ["19", "18 LTS", "17.3 LTS", "16.4 LTS", "15.4 LTS", "14.3 LTS"], serverless_env: ["v1", "v2", "v3", "v4", "v5", "v6"]}
status: VERIFIED
preview: false
related: [azure.databricks.workflows, azure.unity-catalog.securable-model, azure.spark.execution-model, azure.finops.cost-management-and-dbu, azure.observability.monitor-log-analytics, azure.keyvault.secrets-and-rbac]
---

# Azure Databricks — runtime e compute

## Runtimes suportados (2026-10-06)

| DBR | LTS | Spark | Release | Fim de suporte |
|---|---|---|---|---|
| 19 | não | 4.2.0 | 2026-06-15 | definido na transição para LTS |
| 18 | sim | 4.1.0 | 2026-06-10 | 2029-06-10 |
| 17.3 | sim | 4.0.0 | 2025-10-22 | 2028-10-22 |
| 16.4 | sim | 3.5.2 | 2025-05-09 | 2028-05-09 |
| 15.4 | sim | 3.5.0 | 2024-08-19 | 2027-08-19 |
| 14.3 | sim | 3.5.0 | 2024-02-01 | 2027-02-01 |

- Ambiente DBR 18 LTS: Ubuntu 24.04.4, JDK 21 (Zulu21), Scala 2.13.16, Python 3.12.3,
  R 4.5.1, Delta 4.2.0. DBR 15.4 LTS: Java 8, Scala 2.12.15, Python 3.11.11, Delta 3.2.0.
- DBR 18: UDFs Python em UC usam Arrow por padrão; TIMESTAMP em UDF não carrega mais
  `tzinfo` (restaurar com `replace(tzinfo=timezone.utc)`).
- Matriz célula a célula: `knowledge/matrices/databricks-runtime.yaml`.

## Photon

- Engine vetorizado nativo (C++). Default em SQL warehouses e serverless.
- Compute clássico: ligado por default na UI, mas via Clusters/Jobs API é preciso
  `runtime_engine=PHOTON` (Pipelines API: `photon=true`).
- Não acelera UDF, RDD nem Dataset API; streaming só **stateless**.
- Instâncias Photon têm **taxa de DBU diferente** (multiplicador não verificado).

## Serverless

- Serverless compute para notebooks/jobs usa **environment versions** (API Spark Connect
  estável, suporte de 3 anos): v6 (Python 3.12.3, DB Connect 19, EOS 2029-09-03) … v1
  (Python 3.10.12, EOS 2027-03-12).
- Uso de environment versions em compute clássico ("Environments") é **Beta/PREVIEW**.
- Serverless não expõe event log entregue nem dimensionamento de executores.

## Tipos de compute

| Tipo | Uso | Observação |
|---|---|---|
| All-purpose | interativo/notebooks | cobra enquanto ligado; autoterminação importa |
| Job compute | jobs agendados | criado e destruído por run |
| Serverless jobs/notebooks | sem gestão de cluster | environment version |
| SQL warehouse | SQL/BI | Photon default |

Preço/DBU por SKU: `system.billing.usage` e `system.billing.list_prices`
(ver `azure.finops.cost-management-and-dbu`).

## Access modes

- **Standard** (antigo shared; recomendado para compute clássico): isolamento Lakeguard,
  Spark Connect; sem RDD, sem R, sem GPU, sem DBR ML, sem spark-submit task; Hive UDF não
  suportada; DBUtils só lê cloud storage via **external location** UC.
- **Dedicated** (antigo single user): para workloads que dependem dessas features.
- DBR 19+ em standard: configs como `spark.driver.extraJavaOptions`, `spark.jars*`,
  `spark.executorEnv.*`, `spark.pyspark.python` são **rejeitadas na criação** do cluster —
  remover de policies e jobs antes de upgrade.

## Cluster policies

- Restringem/defaultam atributos (tipo de nó, autoterminação, tags, DBR). Fato útil para o
  Forge: política ausente ou permissiva em workspace com jobs caros.
- (Detalhes de policy families não relidos — UNVERIFIED.)

## Secrets

- Escopos **Azure Key Vault-backed** (interface **somente leitura**; segredos geridos no
  Azure) ou **Databricks-backed**.
- AKV-backed **só suporta o modelo Vault access policy**, não Azure RBAC — conflito direto
  com o default RBAC do Key Vault a partir da API 2026-02-01 (ver
  `azure.keyvault.secrets-and-rbac`).
- ACL por escopo (READ/WRITE/MANAGE); `dbutils.secrets.get` redige para `[REDACTED]`, mas
  redação não impede transformação deliberada do valor.
- Secrets como securables UC existem (página "Secrets in Unity Catalog").

## System tables e audit

- Catálogo `system`; exige workspace com UC. Acesso: `USE CATALOG`, `USE SCHEMA`,
  `SELECT`. Tabelas: `system.billing.usage` (global, 365 d), `system.billing.list_prices`,
  `system.access.audit` (**Public Preview**), `system.compute.clusters`,
  `system.compute.node_timeline` (90 d), `system.lakeflow.jobs`,
  `system.lakeflow.job_run_timeline`, `system.query.history`, `system.access.table_lineage`.
- Sem monitoramento em tempo real: dados atualizados ao longo do dia.
- Diagnostic logs via Azure Monitor diagnostic settings exigem **Premium**; latência
  típica ~15 min sem garantia. Databricks recomenda `system.access.audit`.

## Não verificado

- Multiplicador de DBU do Photon; detalhes de cluster policy families.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/18 (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/photon (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/environment-version/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/security/secrets/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/account-settings/audit-log-delivery (retrieved: 2026-10-06)
