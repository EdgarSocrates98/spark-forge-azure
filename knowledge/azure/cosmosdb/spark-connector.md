---
id: azure.cosmosdb.spark-connector
title: Conector Spark do Azure Cosmos DB for NoSQL - artefato, matriz de versões, autenticação e Catalog API
domain: azure-cosmos-db
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/tutorial-spark-connector
    retrieved: 2026-11-03
  - url: https://learn.microsoft.com/en-us/java/api/overview/azure/cosmos-spark_3-1_2-12-readme?view=azure-java-stable
    retrieved: 2026-11-03
  - url: https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3-5_2-12/README.md
    retrieved: 2026-11-03
  - url: https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md
    retrieved: 2026-11-03
  - url: https://github.com/Azure/azure-sdk-for-java/tree/main/sdk/cosmos
    retrieved: 2026-11-03
verified_at: 2026-11-03
versions: {azure-cosmos-spark_3-5_2-12: ["4.29.0-4.50.0"], azure-cosmos-spark_3-4_2-12: ["<=4.50.0"], azure-cosmos-spark_3-3_2-12: ["<=4.50.0"]}
status: VERIFIED
preview: false
related: [azure.cosmosdb.model-and-limits, azure.cosmosdb.bulk-and-batch, azure.cosmosdb.reads-and-tuning, azure.cosmosdb.change-feed, azure.databricks.runtime-and-compute, azure.entra.managed-identity]
---

# Conector Spark do Azure Cosmos DB for NoSQL

O conector OLTP Spark 3 (`com.azure.cosmos.spark:azure-cosmos-spark_<spark>-<scala>`) provê
os formatos `cosmos.oltp` (leitura/escrita transacional) e `cosmos.oltp.changeFeed` (somente
leitura, streaming e batch) e a Catalog API `com.azure.cosmos.spark.CosmosCatalog`.
Cobre apenas a API for NoSQL — não é o conector de Mongo/Cassandra/Gremlin/Table nem o
conector OLAP do Azure Synapse Link (`cosmos.olap`).

## Artefato e matriz de compatibilidade (README oficial)

| Artefato Maven | Spark | JVM | Scala | Databricks Runtime | Fabric Runtime |
|---|---|---|---|---|---|
| `azure-cosmos-spark_3-5_2-12` (até 4.50.0) | 3.5.0 | 8, 11, 17 | 2.12 | 14.*, 15.*, 16.4 LTS | 1.3.* (a partir de 4.41.0) |
| `azure-cosmos-spark_3-4_2-12` (até 4.50.0) | 3.4.0–3.4.1 | 8, 11 | 2.12 | 13.* | — |
| `azure-cosmos-spark_3-3_2-12` (até 4.50.0) | 3.3.0–3.3.2 | 8, 11 | 2.12 | 11.*, 12.* | — |
| `azure-cosmos-spark_3-2_2-12` | 3.2.x | 8, 11 | 2.12 | 10.* | — |
| `azure-cosmos-spark_3-1_2-12` | 3.1.x | 8, 11 | 2.12 | 8.*, 9.* | — |

- A aplicação Scala deve usar a mesma versão de Scala para a qual o Spark foi compilado.
- Java 8 anterior a 8u371 está depreciado em Spark 3.5.0.
- `spark.cosmos.write.bulk.transactional` exige Spark 3.5 ou superior.
- Tutorial oficial usa DBR 13.3 LTS (Spark 3.4.1, Scala 2.12) + Maven Central
  `com.azure.cosmos.spark` com Artifact ID `azure-cosmos-spark_3-4_2-12`.

## Configuração base

```python
config = {
  "spark.cosmos.accountEndpoint": "https://<conta>.documents.azure.com:443/",
  "spark.cosmos.accountKey": "<chave>",            # via secret scope, nunca inline
  "spark.cosmos.database": "<db>",
  "spark.cosmos.container": "<container>",
}
```

Para `ServicePrincipal` são obrigatórios `spark.cosmos.account.subscriptionId`,
`spark.cosmos.account.tenantId`, `spark.cosmos.account.resourceGroupName` e
`spark.cosmos.auth.aad.clientId`/`clientSecret`. `spark.cosmos.account.azureEnvironment`
seleciona cloud soberano (`Azure`, `AzureChina`, `AzureUsGovernment`, `AzureGermany`, `Custom`).

## Autenticação (`spark.cosmos.auth.type`)

- `MasterKey` (default): chaves primárias/secundárias de leitura-escrita ou somente leitura.
- `ServicePrincipal`: Entra ID com `subscriptionId`/`tenantId`/`resourceGroupName` +
  `spark.cosmos.auth.aad.clientId` e `spark.cosmos.auth.aad.clientSecret`.
- `ManagedIdentity`: requer ambiente Spark com identidade gerenciada — funciona em
  Azure Databricks e HDInsight recentes; **não** em Synapse, Fabric ou linked services
  (segundo a referência de configuração oficial; verificar por ambiente antes de prometer).

## Catalog API e DDL

```python
spark.conf.set("spark.sql.catalog.cosmosCatalog", "com.azure.cosmos.spark.CosmosCatalog")
# CREATE DATABASE IF NOT EXISTS cosmosCatalog.<db>
# CREATE TABLE ... USING cosmos.oltp TBLPROPERTIES(
#   partitionKeyPath = '/category', autoScaleMaxThroughput = '1000')
# HPK: partitionKeyPath = '/organization,/department,/team'; manualThroughput = '400'
```

## Formatos de data source

- `cosmos.oltp`: `spark.read`/`spark.write` batch e `writeStream` sink (change feed é fonte).
- `cosmos.oltp.changeFeed`: `readStream` e `read` (batch) somente leitura.
- `SaveMode.Overwrite` no `cosmos.oltp` recria o contêiner (drop+create) — usar só quando a
  recriação é intencional; Append/Ignore/ErrorIfExist seguem semântica normal do Spark.

## Armadilhas verificadas na documentação

- A chave de conta em `spark.cosmos.accountKey` é segredo: nunca em código commitado nem em
  logs (usar secret scope/Key Vault; ver `azure.entra.managed-identity`).
- O conector aplica `spark.cosmos.read.forceEventualConsistency=true` por padrão — leituras
  via Spark usam consistência eventual mesmo quando a conta exige nível mais forte.
- Versões do conector evoluem rápido: confirmar sempre a matriz do README do artefato
  exato (`3-5`, `3-4`, `3-3`, `3-2`, `3-1`) antes de afirmar compatibilidade.

## Fontes

- https://learn.microsoft.com/en-us/azure/cosmos-db/tutorial-spark-connector (retrieved: 2026-11-03)
- https://learn.microsoft.com/en-us/java/api/overview/azure/cosmos-spark_3-1_2-12-readme?view=azure-java-stable (retrieved: 2026-11-03)
- https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3-5_2-12/README.md (retrieved: 2026-11-03)
- https://github.com/Azure/azure-sdk-for-java/blob/main/sdk/cosmos/azure-cosmos-spark_3/docs/configuration-reference.md (retrieved: 2026-11-03)
- https://github.com/Azure/azure-sdk-for-java/tree/main/sdk/cosmos (retrieved: 2026-11-03)
