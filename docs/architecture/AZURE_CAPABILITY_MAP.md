# Azure Capability Map

> Fase 0, item 8 (§294). Mapa do domínio Azure → módulo → artefatos analisados → status.
> Status canônico vive em `parity.yaml`/`manifest.json`; este mapa é a vista de navegação.

```text
Azure Data Engineering
├── Compute ─────────── Azure Databricks · Fabric Spark · Synapse Spark · Spark genérico
├── Storage ─────────── ADLS Gen2 · OneLake · Blob
├── Lakehouse ───────── Delta · Iceberg · Parquet
├── Integration ─────── ADF · Fabric Data Factory · Synapse Pipelines · Databricks Workflows · Airflow
├── Streaming ───────── Event Hubs (+Kafka) · Fabric RTI · Structured Streaming
├── Governance ──────── Unity Catalog · Purview · OneLake/Fabric governance · RBAC · ACL
├── Identity/Security ─ Entra ID · Managed Identity · Service Principal · Key Vault · Private Link/DNS
├── Observability ───── Azure Monitor · Log Analytics · Databricks system tables · Fabric monitoring
└── FinOps ──────────── Cost Management · Fabric capacity · Databricks economics
```

| Domínio | Módulo `sparkforge_azure/…` | Artefatos de entrada (offline) | Collector (opt-in, read-only) | Skill | Specialist |
|---|---|---|---|---|---|
| Spark genérico | `spark/` | PySpark, Spark SQL, event log JSON, `spark.conf` | — | `azure-spark`, `spark-performance`, `spark-streaming` | Spark Performance |
| Azure Databricks | `azure/databricks/` | cluster/job/policy JSON, notebooks `.py` (`# COMMAND`), DAB `databricks.yml` | Databricks jobs/clusters | `azure-databricks` | Azure Databricks |
| Unity Catalog | `azure/unity_catalog/` | grants JSON, external locations, storage credentials, bindings | UC API | `unity-catalog` | Unity Catalog |
| Fabric | `azure/fabric/` | item definitions, notebook source, capacity metrics export | Fabric REST (metadata) | `fabric-data-engineering`, `fabric-onelake`, `fabric-realtime` | Fabric, OneLake |
| Synapse | `azure/synapse/` | Spark pool JSON, pipeline JSON, linked services | Synapse REST | `azure-synapse` | Synapse |
| ADF | `azure/adf/` | pipeline/linked service/dataset/trigger/IR JSON (ARM export) | ADF runs | `azure-data-factory` | ADF |
| ADLS Gen2 | `azure/storage/` | ACL dumps, RBAC assignments, storage account JSON | ADLS metadata | `azure-adls` | ADLS |
| Event Hubs | `azure/eventhubs/` | namespace/hub JSON, Spark Kafka options | Event Hubs metadata | `azure-event-hubs` | Event Hubs, Streaming |
| Purview | `azure/purview/` | lineage/scan exports | Purview | `azure-purview` | Purview |
| Entra / identity | `azure/identity/` | role assignments, MI/SP descriptors | ARG | `azure-entra` | Entra |
| Networking | `azure/network/` | VNet/PE/DNS zone JSON, NSG | ARG | `azure-networking` | Networking |
| Key Vault | `azure/identity/keyvault.py` | vault JSON, secret scope refs | ARG | `azure-entra` | Entra |
| Governance (multicamada) | `azure/governance/` | composição dos acima | — | `unity-catalog`, `azure-adls` | Unity Catalog + ADLS + Entra + Networking |
| Observability | `azure/observability/` | Log Analytics exports, system tables exports | Azure Monitor / Log Analytics | `azure-observability` | Observability |
| FinOps | `azure/finops/` | Cost export CSV, `system.billing.usage` export, capacity metrics | Cost Management | `azure-finops` | FinOps |
| IaC | `azure/iac/` | Terraform `azurerm`/`databricks`, Bicep | — | `azure-terraform`, `azure-bicep` | Terraform, Bicep |
| Delta / Iceberg | `lakehouse/` | `_delta_log` JSON, Iceberg metadata JSON | — | `delta-lake`, `iceberg` | Delta, Iceberg |
| Migration | `migration/` | `case.yaml` + `estate.json`/`assessment.json`/`environment.json`/`validation.json` + `notebooks/` | — (exports ADF/Synapse/Fabric injetados; live é opt-in) | `azure-data-factory`, `azure-synapse` | Migration |

Composição static+live somente por ID explícito (ARM resource ID, Databricks workspace ID, Fabric
workspace/item GUID), nunca por nome parecido (§64).
