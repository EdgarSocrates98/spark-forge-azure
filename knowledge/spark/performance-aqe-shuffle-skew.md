---
id: azure.spark.performance-aqe-shuffle-skew
title: Performance Spark - AQE, shuffle, skew, joins, sizing e small files
domain: spark-performance
authority: apache_official
sources:
  - url: https://spark.apache.org/docs/latest/sql-performance-tuning.html
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/photon
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/clustering
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {spark: ["4.2.0"]}
status: VERIFIED
preview: false
related: [azure.spark.execution-model, lakehouse.delta-lake, azure.adls.gen2, azure.databricks.runtime-and-compute]
---

# Performance Spark — AQE, shuffle, skew, joins, sizing e small files

## Resumo

Antes de mexer em config: medir. O Forge só recomenda a partir de fatos (plano, event log,
métricas de task) e nunca promete percentual de ganho. Os defaults abaixo são os da doc do
Apache Spark 4.2.0 lida em 2026-10-06; runtimes gerenciados podem sobrescrever.

## Defaults relevantes (Spark 4.2.0)

| Config | Default | Papel |
|---|---|---|
| `spark.sql.adaptive.enabled` | true | AQE: reotimiza com estatísticas de runtime |
| `spark.sql.adaptive.coalescePartitions.enabled` | true | junta partições pequenas pós-shuffle |
| `spark.sql.adaptive.advisoryPartitionSizeInBytes` | 64 MB | tamanho-alvo de partição pós-shuffle |
| `spark.sql.adaptive.skewJoin.enabled` | true | divide partições enviesadas em sort-merge join |
| `spark.sql.adaptive.skewJoin.skewedPartitionFactor` | 5.0 | skew = > fator × mediana… |
| `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` | 256 MB | …e > este limiar |
| `spark.sql.adaptive.autoBroadcastJoinThreshold` | (herda) | default = `spark.sql.autoBroadcastJoinThreshold` |
| `spark.sql.adaptive.localShuffleReader.enabled` | true | evita shuffle quando não precisa |
| `spark.sql.shuffle.partitions` | 200 | partições iniciais de shuffle |
| `spark.sql.files.maxPartitionBytes` | 128 MB | tamanho de split de leitura |
| `spark.sql.autoBroadcastJoinThreshold` | 10 MB | broadcast automático |

## Shuffle e partições

- Com AQE ligado, `spark.sql.shuffle.partitions` vira número **inicial**; o coalesce reduz.
  Valor fixo alto demais ainda gera overhead de agendamento antes do coalesce.
- `repartition(n)` força shuffle; `coalesce(n)` reduz sem shuffle completo (pode desbalancear).
- `repartition(1)` antes de write serializa a escrita em uma task: fato a sinalizar.

## Skew

- Sintoma: max duração de task ≫ mediana no mesmo stage; spill concentrado; poucas tasks
  terminando por último.
- AQE trata skew **apenas em sort-merge join** com os dois limiares acima.
- Skew em `groupBy`/window não é corrigido pelo skew join: opções são salting, pré-agregação
  ou mudar a chave.
- Chaves nulas ou "default" (ex.: `''`, `-1`) são causa frequente.

## Joins

- Hints suportados: `BROADCAST`/`BROADCASTJOIN`/`MAPJOIN`, `MERGE`, `SHUFFLE_HASH`,
  `SHUFFLE_REPLICATE_NL`.
- Broadcast de tabela grande pressiona memória do driver e executores; hint não verifica
  tamanho.
- Join explodindo (cardinalidade N×M) é bug de dados, não de tuning.

## Cache e checkpoint

- `cache()`/`persist()` só compensa com ≥ 2 ações sobre o mesmo DataFrame; sem `unpersist`
  ocupa memória de storage.
- `checkpoint()`/`localCheckpoint()` cortam lineage longa (loops iterativos); checkpoint
  confiável grava em storage.
- Em Delta, reler a tabela costuma ser melhor que cachear o DataFrame de escrita.

## Executores e memória

- Dimensionar por dados por task, não por "mais nós": partição pós-shuffle muito maior que
  o advisory (64 MB) + spill → aumentar partições antes de aumentar memória.
- Photon (Databricks) não acelera UDF Python/RDD/Dataset API; e tem taxa de DBU diferente.
- Fabric: Native Execution Engine (Gluten+Velox), `spark.native.enabled`, disponível em
  Runtime 1.3 e 2.0. O "até 6x" em TPC-DS SF1000 é **claim do fornecedor**, não baseline.

## File sizing e small files

- ADLS: recomendação oficial de arquivos entre **256 MB e 100 GB**; operações cobradas em
  incrementos de 4 MB; muitos arquivos pequenos aumentam overhead por arquivo.
- Delta: `OPTIMIZE` compacta; liquid clustering faz clustering incremental (ver
  `lakehouse.delta-lake`). Partição Hive com cardinalidade alta gera small files.
- Streaming com trigger curto gera arquivos pequenos por micro-batch: compactar periodicamente.

## Fatos que o Forge extrai

| Fato | Evidência | Achado possível |
|---|---|---|
| `shuffle.partitions` fixo + AQE off | conf do job | revisar AQE |
| razão max/mediana de task > limiar | event log | skew provável (não certo) |
| `repartition(1)` antes de write | AST | gargalo de escrita |
| UDF Python com equivalente nativo | AST | trocar por função built-in |
| arquivos médios < 32 MB na tabela | `DESCRIBE DETAIL` | small files |

## O que NÃO afirmar

- "Ligar AQE reduz X%": sem baseline não há número.
- "Broadcast sempre é mais rápido": depende de tamanho e memória.

## Não verificado

- Overrides de default específicos de cada runtime gerenciado (Databricks/Fabric/Synapse)
  não foram conferidos página a página.

## Fontes

- https://spark.apache.org/docs/latest/sql-performance-tuning.html (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/photon (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/clustering (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime (retrieved: 2026-10-06)
