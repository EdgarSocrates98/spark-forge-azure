---
id: azure.spark.execution-model
title: Modelo de execução do Spark nos runtimes Azure
domain: azure-spark
authority: apache_official
sources:
  - url: https://spark.apache.org/docs/latest/sql-performance-tuning.html
    retrieved: 2026-10-06
  - url: https://spark.apache.org/news/index.html
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {spark: ["4.2.0", "4.1.0", "4.0.0", "3.5.x"]}
status: VERIFIED
preview: false
related: [azure.spark.performance-aqe-shuffle-skew, azure.spark.streaming-state-checkpoint, azure.databricks.runtime-and-compute, azure.fabric.data-engineering-spark, azure.synapse.spark-runtimes]
---

# Modelo de execução do Spark nos runtimes Azure

## Resumo

Spark executa um plano lógico (DataFrame/SQL) que o otimizador Catalyst transforma em plano
físico; o plano é quebrado em **jobs** (um por ação), **stages** (fronteira = shuffle) e
**tasks** (uma por partição). O driver agenda; executores rodam tasks. Nos três serviços Azure
o motor é o mesmo Apache Spark, mas runtime, versão e extensões mudam — e é isso que o Forge
precisa saber antes de qualquer recomendação.

## Hierarquia de execução

| Nível | Fronteira | Onde observar |
|---|---|---|
| Application | uma SparkSession/cluster | Spark UI, event log |
| Job | cada ação (`count`, `write`, `collect`) | aba Jobs |
| Stage | wide transformation → shuffle (`groupBy`, `join`, `repartition`) | aba Stages, DAG |
| Task | uma partição de um stage | métricas por task (duração, spill, shuffle read) |

- **Narrow** (`filter`, `select`, `withColumn`) não cria stage; **wide** cria e grava shuffle.
- O número de tasks de um stage pós-shuffle parte de `spark.sql.shuffle.partitions`
  (default **200**) e é reajustado em runtime pelo AQE (ver
  `azure.spark.performance-aqe-shuffle-skew`).
- Leitura de arquivo: partições de input limitadas por `spark.sql.files.maxPartitionBytes`
  (default **128 MB**).
- `spark.sql.adaptive.enabled` é **true** por default na doc do Spark 4.2.0 lida.

## Versões de Spark por serviço (2026-10-06)

| Serviço | Runtime | Apache Spark |
|---|---|---|
| Azure Databricks | 19 (não LTS) | 4.2.0 |
| Azure Databricks | 18 LTS | 4.1.0 |
| Azure Databricks | 17.3 LTS | 4.0.0 |
| Azure Databricks | 16.4 LTS | 3.5.2 |
| Azure Databricks | 15.4 LTS / 14.3 LTS | 3.5.0 |
| Fabric | Runtime 2.0 (GA) | 4.1 (4.1.1) |
| Fabric | Runtime 1.3 (EOSA) | 3.5 (3.5.5) |
| Synapse | Spark 3.5 (GA) | 3.5 |

Fonte canônica com célula a célula: `knowledge/matrices/databricks-runtime.yaml`,
`fabric-runtime.yaml`, `synapse-runtime.yaml`.

**Discrepância conhecida:** a doc do DBR 19 cita Spark 4.2.0 com release em 15/06/2026; o
spark.apache.org lista Spark 4.2.0 em 14/07/2026. Não afirmar a data de release do 4.2.0
sem citar as duas fontes (status CONFLICTED na matriz).

## Spark Connect vs Spark Classic

- No Databricks, compute **standard** (antigo "shared") usa Spark Connect, que "adia análise
  e resolução de nomes para o momento da execução" — erros de coluna inexistente podem
  aparecer só na ação, não na transformação.
- Em standard access mode: RDD API não é suportada; `sc`/`sparkContext` não são suportados
  para Scala; para Python, `sc` exige DBR 14.0+.
- Consequência para o analisador estático: uso de `rdd`, `sparkContext` ou `mapPartitions`
  Scala é fato relevante para compatibilidade de access mode, não para performance.

## Memória e executores (conceitos)

- Executor = JVM com N cores; cada core roda uma task por vez.
- Memória unificada (execução + storage) dentro do heap; o excedente vira **spill** para disco.
- Spill alto + GC alto em poucas tasks costuma indicar skew, não falta de memória global.
- `collect()`/`toPandas()` trazem dados ao driver: risco de OOM no driver.
- Em Databricks e Fabric o dimensionamento é por tipo de nó/pool; em serverless não há
  controle de executor (ver `azure.databricks.runtime-and-compute`).

## O que o Forge observa (fatos determinísticos)

- Ações dentro de loop (`for ... : df.count()`), `collect` sem limite, UDF Python onde há
  função nativa, `repartition(1)` antes de write, `cache()` sem reuso.
- Event log: duração por stage, `shuffle read/write bytes`, `spill (memory/disk)`, max vs
  mediana de duração de task (indicador de skew).

## O que NÃO afirmar

- Não prometer ganho de tempo/custo por mudar uma config sem baseline medido.
- Não presumir versão de Spark pelo nome do cluster; ler `spark_version` ou o runtime.
- Não tratar Photon/Native Execution Engine como Spark puro: são motores vetorizados
  diferentes com cobertura parcial de operadores.

## Não verificado

- Data de release do Spark 4.2.0 (discrepância DBR 19 × spark.apache.org).

## Fontes

- https://spark.apache.org/docs/latest/sql-performance-tuning.html (retrieved: 2026-10-06)
- https://spark.apache.org/news/index.html (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/release-notes/runtime/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/compute/standard-limitations (retrieved: 2026-10-06)
