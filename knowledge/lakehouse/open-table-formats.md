---
id: lakehouse.open-table-formats
title: Matriz de decisão - Delta vs Iceberg vs Parquet no Azure
domain: open-table-formats
authority: internal
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/delta/iceberg-reads
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    retrieved: 2026-10-06
  - url: https://iceberg.apache.org/spec/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [lakehouse.delta-lake, lakehouse.iceberg, azure.fabric.onelake-shortcuts, azure.unity-catalog.securable-model]
---

# Matriz de decisão — Delta vs Iceberg vs Parquet no Azure

## Resumo

No Azure, **Delta é o formato nativo** de Databricks e Fabric (lakehouse "Tables" só
descobre Delta; SQL analytics endpoint só mostra Delta). Iceberg entra por
interoperabilidade (UC Iceberg REST, managed Iceberg no Databricks, shortcuts Iceberg no
OneLake). Parquet puro serve para troca de arquivos e landing, não para tabela com DML.
Esta matriz é síntese **interna** (authority: internal) a partir das fontes listadas.

## Matriz

| Critério | Delta Lake | Apache Iceberg | Parquet puro |
|---|---|---|---|
| Interoperabilidade Azure | nativo Databricks + Fabric | UC Iceberg REST; Fabric via shortcut; leitura de Delta via UniForm | universal, sem semântica de tabela |
| Governança | UC (managed/external), OneLake catalog/Purview | UC managed Iceberg; demais catálogos externos | só ACL/RBAC de arquivo |
| Engines | Spark, Databricks SQL, Fabric (Spark, SQL endpoint, Direct Lake) | Spark, engines Iceberg externos; Databricks managed | qualquer |
| Streaming | source/sink Structured Streaming maduro; CDF | suportado no Spark (não detalhado aqui) | file sink exactly-once, sem ACID multi-arquivo |
| DML | MERGE/UPDATE/DELETE, DV, row-level concurrency | MERGE/UPDATE/DELETE (CoW/MoR); v3 com DV | nenhum (reescrita manual) |
| Layout | liquid clustering (GA DBR 15.4 LTS+) | partition evolution; liquid clustering managed (Preview Iceberg) | particionamento Hive |
| Ops | OPTIMIZE, VACUUM, predictive optimization | expire snapshots, compactação, órfãos | compactação manual |
| Complexidade operacional | baixa no Databricks/Fabric | média (catálogo é decisão sua) | baixa, mas sem garantias |
| Migração | Delta → Iceberg reads sem reescrever dados | Iceberg → Delta exige conversão | Parquet → Delta: `CONVERT TO DELTA` (não relido) |

## Heurística do Forge

1. Workload só Databricks/Fabric → **Delta** (managed UC quando possível).
2. Consumidor externo Iceberg somente leitura → **Delta + Iceberg reads (UniForm)**;
   cuidado: deletion vectors bloqueiam leitura Iceberg v2.
3. Escrita multi-engine Iceberg → **Iceberg managed/REST catalog**, com catálogo explícito.
4. Landing/troca → Parquet (ou Avro para write-heavy, como Event Hubs Capture).

## Armadilhas

- Habilitar features (DV, clustering, IcebergCompatV2) eleva protocolo **sem downgrade**:
  verificar leitores antes.
- Fabric Runtime 2.0: features específicas Delta 4.2 são experimentais/Spark-only — não
  usar em tabelas lidas por outros engines Fabric.
- Shortcut em Fabric com espaço no nome não é reconhecido como tabela Delta.

## Não verificado

- `CONVERT TO DELTA` e streaming Iceberg no Spark: não relidos nesta verificação.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/delta/iceberg-reads (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/clustering (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts (retrieved: 2026-10-06)
- https://iceberg.apache.org/spec/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices (retrieved: 2026-10-06)
