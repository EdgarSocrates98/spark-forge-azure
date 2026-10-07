---
id: lakehouse.iceberg
title: Apache Iceberg no Azure - snapshots, evolução, MERGE, ADLS e catálogos
domain: iceberg
authority: apache_official
sources:
  - url: https://iceberg.apache.org/spec/
    retrieved: 2026-10-06
  - url: https://iceberg.apache.org/docs/latest/spark-configuration/
    retrieved: 2026-10-06
  - url: https://github.com/apache/iceberg/releases
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/features/deletion-vectors
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/delta/iceberg-reads
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {iceberg: ["1.12.0"], iceberg_spec: ["v1", "v2", "v3"]}
status: VERIFIED
preview: false
related: [lakehouse.delta-lake, lakehouse.open-table-formats, azure.unity-catalog.securable-model, azure.fabric.onelake-shortcuts]
---

# Apache Iceberg no Azure

## Resumo

Iceberg é um formato de tabela aberto: Parquet/ORC/Avro + metadados (metadata JSON →
manifest list → manifests) versionados por **snapshot**. Versão mais recente do projeto:
**1.12.0** (2026-09-30). Spec v1, v2 e v3 publicadas. No Azure, o **catálogo** é a decisão
central — e **não existe Glue** aqui: nunca presumir `type=glue`.

## Snapshots e time travel

- Cada commit gera um snapshot; leitores escolhem snapshot por id ou timestamp.
- Expirar snapshots (`expire_snapshots`) e remover órfãos são manutenção obrigatória —
  equivalente funcional ao VACUUM do Delta. (Nomes exatos de procedures: ver doc Spark do
  Iceberg; não relidos aqui.)

## Evolução de schema e partição

- Schema evolution por id de coluna (rename/drop/reorder sem reescrita).
- **Partition evolution**: mudar a especificação sem reescrever dados antigos; transforms
  ocultas (`bucket`, `truncate`, `year/month/day/hour`).
- No Databricks, em Iceberg managed, partições são interpretadas como **chaves de liquid
  clustering**; `bucket(c1, 10)` vira cluster por `c1`.

## Spec v3 (adotada)

Adiciona: timestamps em nanossegundos, tipos `unknown`, `variant`, `geometry`, `geography`,
default values, transforms multi-argumento, **row lineage**, **binary deletion vectors**,
chaves de criptografia. Iceberg 1.10.0 adicionou leitores de row lineage v3.

## MERGE / UPDATE / DELETE

- Suportados via extensões SQL do Iceberg no Spark (copy-on-write ou merge-on-read com
  delete files).
- Merge-on-read acumula delete files: exige compactação periódica.
- Databricks: Iceberg v3 managed suporta deletion vectors, row tracking e row-level
  concurrency em DBR 18.0+; Iceberg v2 managed **não** tem row-level concurrency.

## Catálogos (configuração Spark)

`spark.sql.catalog.<nome>` com `type` ∈ `hive`, `hadoop`, `rest`, `glue`, `nessie`, `jdbc`,
ou `catalog-impl` customizado; `warehouse` define localização; `io-impl` troca a camada de
storage.

| Cenário Azure | Catálogo recomendado | Observação |
|---|---|---|
| Databricks + UC | Unity Catalog (Iceberg REST Catalog API) | managed Iceberg ou Delta com Iceberg reads |
| OSS Spark em ADLS | `rest` (UC, Polaris/outro) ou `jdbc` | `hadoop` sem catálogo não tem locking robusto |
| Fabric | shortcuts Iceberg no OneLake | leitura via virtualização de metadados |
| `glue` | **não aplicável** | serviço AWS |

## Armazenamento em ADLS Gen2

- Caminho `abfss://<container>@<conta>.dfs.core.windows.net/<path>`.
- Permissões seguem RBAC → ABAC → ACL do ADLS (ver `azure.adls.gen2`).
- Arquivos pequenos pesam igual ao Delta: cobrança em incrementos de 4 MB.

## Interoperabilidade com Delta

- Delta com Iceberg reads (UniForm) expõe metadados Iceberg **somente leitura**;
  deletion vectors Delta não são suportados por leitura Iceberg v2.
- Iceberg v3 aceita deletion vectors; CDF **não** faz parte da spec Iceberg (leitores
  Iceberg externos não leem CDF automático do Databricks).

## O que NÃO afirmar

- Que um job Iceberg "usa Glue" ou "Lake Formation" no Azure.
- Que Iceberg v4 existe/é adotado (não verificado).

## Não verificado

- FileIO específico de ADLS (`ADLSFileIO`) e suas configs: não relidos nesta verificação.
- Nomes exatos de procedures Spark (`rewrite_data_files`, `expire_snapshots`,
  `remove_orphan_files`): não relidos (UNVERIFIED).
- Status de spec v4.

## Fontes

- https://iceberg.apache.org/spec/ (retrieved: 2026-10-06)
- https://iceberg.apache.org/docs/latest/spark-configuration/ (retrieved: 2026-10-06)
- https://github.com/apache/iceberg/releases (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/clustering (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/features/deletion-vectors (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/delta/iceberg-reads (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts (retrieved: 2026-10-06)
