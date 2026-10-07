---
id: lakehouse.delta-lake
title: Delta Lake - DML, OPTIMIZE, VACUUM, time travel, CDF, clustering, DV e UniForm
domain: delta-lake
authority: databricks_official
sources:
  - url: https://docs.delta.io/latest/delta-utility.html
    retrieved: 2026-10-06
  - url: https://github.com/delta-io/delta/releases
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/features/deletion-vectors
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/features/change-data-feed
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/delta/iceberg-reads
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {delta_oss: ["4.4.1", "4.3.0", "4.2.0"], dbr: ["19", "18 LTS", "17.3 LTS", "16.4 LTS", "15.4 LTS"]}
status: VERIFIED
preview: false
related: [lakehouse.iceberg, lakehouse.open-table-formats, azure.spark.performance-aqe-shuffle-skew, azure.unity-catalog.securable-model]
---

# Delta Lake — DML, manutenção, histórico e interoperabilidade

## Resumo

Delta = Parquet + transaction log (`_delta_log`). Toda escrita é um commit versionado:
isso dá ACID, time travel e CDF. Manutenção (`OPTIMIZE`, `VACUUM`) é obrigatória em
produção; predictive optimization (UC managed) pode fazer isso automaticamente.
Versões: Delta OSS mais recente **4.4.1** (2026-10-05); Delta 4.4.x construído para
Spark 4.2.0/4.1.0/4.0.1 (Scala 2.13). DBR 18 LTS embarca Delta 4.2.0.

## DML (MERGE / UPDATE / DELETE)

- Sem deletion vectors, alterar uma linha reescreve o arquivo Parquet inteiro.
- `MERGE` com múltiplos matches na origem para a mesma linha-alvo falha: deduplicar a
  origem antes (fato estático a extrair: MERGE sem dedupe/agrupamento da source).
- Concorrência: tabelas com deletion vectors + row tracking suportam **row-level
  concurrency** (DBR 14.2+), reduzindo conflitos entre writers.

## OPTIMIZE e layout

- `OPTIMIZE` compacta arquivos pequenos; em tabela com liquid clustering, faz clustering
  **incremental**. `OPTIMIZE ... FULL` (DBR 16.4 LTS+) reclusteriza tudo.
- `ZORDER` e particionamento são **incompatíveis** com liquid clustering.

## Liquid clustering

- GA para Delta em **DBR 15.4 LTS+**; Public Preview para Iceberg (DBR 16.4 LTS+).
- `CLUSTER BY (c1, c2)`; até **4** chaves; chaves precisam ter estatísticas (por default as
  32 primeiras colunas).
- `CLUSTER BY AUTO` (UC managed, DBR 15.4 LTS+) depende de predictive optimization.
- Conversão de tabela particionada: `ALTER TABLE ... REPLACE PARTITIONED BY WITH CLUSTER BY`
  em **DBR 18.1+**.
- Clustering-on-write só acima de limiares (ex.: 1 chave: 64 MB UC managed / 256 MB outras).
- Habilitar clustering eleva protocolo para writer 7 / reader 3 — **sem downgrade**.
- Fabric Runtime 2.0 (Delta 4.2) suporta liquid clustering.

## Deletion vectors

- Marcam linhas removidas em metadados; leituras aplicam na hora da query.
- Delta: habilitar via `'delta.enableDeletionVectors' = true` (eleva protocolo).
- Leitura DBR 12.2 LTS+; escrita com todas as otimizações DBR 14.3 LTS+; OSS Delta lê DV a
  partir de 2.3.0.
- Aplicação física: `OPTIMIZE`, `REORG TABLE ... APPLY (PURGE)` ou auto-compaction.
  Para remover fisicamente (GDPR): `REORG ... APPLY (PURGE)` seguido de `VACUUM`.
- Incompatível com leituras Iceberg v2 (UniForm IcebergCompatV2).

## VACUUM e retenção

- Retenção default **7 dias**; remove arquivos de dados fora da retenção, **não** os logs.
- Safety check: `spark.databricks.delta.retentionDurationCheck.enabled`.
- Após VACUUM, time travel para versões além da retenção deixa de funcionar.
- Log: `delta.logRetentionDuration` (default 30 dias); arquivos removidos:
  `delta.deletedFileRetentionDuration`.
- `VACUUM` modos FULL (default) e LITE (Delta 3.3+).
- VACUUM na origem quebra **shallow clones** que referenciam seus arquivos.

## Time travel e RESTORE

- `VERSION AS OF` / `TIMESTAMP AS OF`; `DESCRIBE HISTORY` (retenção default 30 dias).
- `RESTORE` é operação que altera dados (`dataChange=true`): streams downstream podem
  reprocessar o restaurado como novo.

## Change Data Feed

- Legacy CDF: `delta.enableChangeDataFeed = true` por tabela; só registra mudanças após
  habilitar. Colunas: `_change_type` (`insert`, `update_preimage`, `update_postimage`,
  `delete`), `_commit_version`, `_commit_timestamp`.
- **Automatic CDF**: DBR 19+, tabelas UC com row tracking (Delta) ou Iceberg v3; só
  leitores Databricks. Não combinar com legacy.
- Leitura: `readChangeFeed=true` + `startingVersion`; SQL `table_changes(...)`.
- CDF não é histórico permanente: some com a retenção; não atravessa mudança de schema não
  aditiva (rename/drop/type change) com column mapping.

## Schema evolution

- Column mapping (`delta.columnMapping.mode` = `name`/`id`) permite rename/drop sem reescrita.
- Mudança não aditiva afeta CDF e leitores streaming (pode exigir restart/novo checkpoint).

## UniForm / Iceberg reads

- DBR 14.3 LTS+; tabela registrada no UC; column mapping obrigatório; protocolo
  reader ≥ 2 / writer ≥ 7; propriedades `delta.enableIcebergCompatV2 = true` e
  `delta.universalFormat.enabledFormats = iceberg`.
- Metadados Iceberg gerados **assíncronos**; clientes Iceberg são **somente leitura**.
- Delta 4.3.0 (OSS) trouxe conversão UniForm Iceberg atômica + incremental.

## Fabric

- Features específicas do Delta 4.2 no Fabric Runtime 2.0 são experimentais e só Spark:
  evitar em tabelas compartilhadas entre engines Fabric.

## O que NÃO afirmar

- Que VACUUM "libera espaço imediatamente" em tabela com shallow clones/time travel ativo.
- Que CDF substitui auditoria permanente.

## Não verificado

- Erro de `MERGE` com múltiplos matches na origem: comportamento amplamente documentado,
  mas a página de MERGE não foi relida nesta verificação (UNVERIFIED).

## Fontes

- https://docs.delta.io/latest/delta-utility.html (retrieved: 2026-10-06)
- https://github.com/delta-io/delta/releases (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/clustering (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/features/deletion-vectors (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/features/change-data-feed (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/delta/iceberg-reads (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0 (retrieved: 2026-10-06)
