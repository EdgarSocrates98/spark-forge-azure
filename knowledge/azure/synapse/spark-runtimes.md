---
id: azure.synapse.spark-runtimes
title: Azure Synapse Spark - runtimes 3.3/3.4 (EOS) e 3.5
domain: azure-synapse
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support
    retrieved: 2026-10-06
  - url: https://spark.apache.org/news/index.html
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/synapse-to-fabric-spark-migration-assistant
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {synapse_spark: ["3.5", "3.4", "3.3"]}
status: VERIFIED
preview: false
related: [migration.synapse-to-fabric, azure.synapse.pipelines-and-linked-services, azure.spark.execution-model, azure.fabric.data-engineering-spark]
---

# Azure Synapse Spark — runtimes

## Situação em 2026-10-06

| Runtime | Release | Estado | EOS anunciado | EOS efetivo |
|---|---|---|---|---|
| Spark 3.5 | 2025-10-13 | GA; LTS a partir de 2027-11-01 (12 meses) | 2027-10-31 | 2028-10-31 |
| Spark 3.4 | 2023-11-21 | "deprecated and soon to be disabled" | 2025-04-30 | **2026-03-31 (passado)** |
| Spark 3.3 | 2022-11-17 | fora de suporte | — | 2025-03-31 |

- **Não há runtime Spark 4.x no Synapse.** A Microsoft recomenda Fabric Runtime 2.0
  (Spark 4.1) para quem precisa de Spark 4.
- Apache Spark 3.4.x é EOL no upstream (último 3.4.4 em 2024-10-27); 3.5.9 é a linha de
  manutenção (2026-07-16).
- Matriz: `knowledge/matrices/synapse-runtime.yaml`.

## Upgrade de pool para 3.5

- **Não** é feito pela UX. Usar PowerShell:
  `Update-AzSynapseSparkPool -SparkVersion 3.5 -ForceApplySetting`.
- Testar libs: pacotes de workspace e de pool compilados para versões anteriores podem
  falhar.

## Riscos que o Forge sinaliza

| Fato | Severidade | Motivo |
|---|---|---|
| Pool em 3.4 ou 3.3 | alta | após EOS efetivo; pode ser desabilitado |
| Pool em 3.5 sem plano | info | EOS efetivo 2028-10-31; LTS a partir de nov/2027 |
| Dependência de Spark 4 API em código Synapse | bloqueio | não existe runtime 4.x |

## Migração para Fabric

- Assistente de migração Synapse → Fabric Spark (pools, notebooks, SJDs, lake databases)
  está em **public preview** (PREVIEW). Ver `migration.synapse-to-fabric`.

## O que NÃO afirmar

- Que o Synapse como um todo será descontinuado em data X: só há depreciações pontuais
  documentadas; a informação de descontinuação total vem de Q&A comunitário
  (UNVERIFIED, não citar como fato).

## Não verificado

- Conteúdo detalhado das páginas de migração (URLs confirmadas por busca, não lidas).

## Fontes

- https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support (retrieved: 2026-10-06)
- https://spark.apache.org/news/index.html (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/synapse-to-fabric-spark-migration-assistant (retrieved: 2026-10-06)
