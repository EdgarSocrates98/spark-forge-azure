---
id: migration.synapse-to-fabric
title: Migração Synapse para Fabric - Spark, pipelines e lacunas conhecidas
domain: migration
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/synapse-to-fabric-spark-migration-assistant
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/how-to-upgrade-your-azure-synapse-analytics-pipelines-to-fabric-data-factory
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {synapse_spark: ["3.5", "3.4"], fabric_runtime: ["2.0", "1.3"]}
status: VERIFIED
preview: true
related: [azure.synapse.spark-runtimes, azure.synapse.pipelines-and-linked-services, azure.fabric.data-engineering-spark, azure.fabric.data-factory]
---

# Migração Synapse → Fabric

> `preview: true` porque o assistente de migração Spark está em **public preview**.

## Motivadores verificados

- Synapse Spark 3.4 passou do EOS efetivo (2026-03-31); 3.5 tem EOS efetivo 2028-10-31.
- **Não há Spark 4.x no Synapse**; a Microsoft recomenda Fabric Runtime 2.0 (Spark 4.1).
- Descontinuação total do Synapse **não** é anúncio oficial verificado (só depreciações
  pontuais). Não usar "Synapse vai acabar" como argumento.

## Spark (pools, notebooks, SJDs, lake databases)

- Assistente Synapse → Fabric Spark (**PREVIEW**): migra pools, notebooks, Spark job
  definitions e lake databases.
- Mapeamento de runtime: Synapse 3.5 (Spark 3.5) → Fabric 1.3 (Spark 3.5, EOSA, LTS até
  mar/2027) ou **2.0** (Spark 4.1, Scala 2.13, Java 21, Python 3.13).
- Ir direto para 2.0 implica migração de Spark 3.5 → 4.1 **e** Scala 2.12 → 2.13: libs
  JVM precisam de rebuild.
- Features Delta 4.2 do 2.0 são experimentais/Spark-only: cuidado com tabelas lidas por
  SQL endpoint/Direct Lake.
- Storage: dados em ADLS podem ficar onde estão via **OneLake shortcuts** (sem cópia),
  respeitando o modelo de identidade dos shortcuts.

## Pipelines

- Guia oficial de upgrade de pipelines Synapse → Fabric Data Factory (URL verificada por
  busca; conteúdo não lido).
- Lacunas confirmadas pela comparação oficial:
  - atividades **Synapse notebook/SJD** não existem no Fabric (reapontar para Fabric
    Notebook);
  - **sem IR**: self-hosted IR → on-premises data gateway / VNet data gateway;
  - managed VNet + managed private endpoints: "a definir";
  - Mapping Data Flow → Dataflow Gen2 com transforms MDF (**PREVIEW**);
  - Synapse Link → Mirroring.

## Checklist determinístico (o que o Forge levanta)

| Item | Fonte do fato | Bloqueia? |
|---|---|---|
| Pools em 3.3/3.4 | ARM/Resource Graph | urgência |
| Libs Scala 2.12 / JARs | pacotes do workspace | bloqueia 2.0 |
| Atividades Synapse notebook/SJD | JSON do pipeline | requer reescrita |
| SHIR / managed VNet | JSON de IR / linked services | requer gateway |
| Mapping Data Flows | JSON | preview no destino |
| Segredos em Key Vault via SHIR | linked services | modelo de credencial muda |

## Não verificado

- Conteúdo das páginas: migrate-synapse-spark-pools, synapse-migration-spark-workloads,
  migrate-synapse-data-pipelines e guia de upgrade de pipelines.

## Fontes

- https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-version-support (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/synapse-to-fabric-spark-migration-assistant (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/how-to-upgrade-your-azure-synapse-analytics-pipelines-to-fabric-data-factory (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0 (retrieved: 2026-10-06)
