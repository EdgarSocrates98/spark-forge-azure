---
id: azure.fabric.data-engineering-spark
title: Fabric Data Engineering - runtimes 1.3/2.0, lakehouse, notebooks e Spark job definitions
domain: fabric-data-engineering
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {fabric_runtime: ["2.0", "1.3"], spark: ["4.1.1", "3.5.5"], delta: ["4.2", "3.2"]}
status: VERIFIED
preview: false
related: [azure.fabric.onelake-shortcuts, azure.fabric.capacity-and-throttling, azure.spark.execution-model, lakehouse.delta-lake, migration.synapse-to-fabric]
---

# Fabric Data Engineering — Spark

## Runtimes (2026-10-06)

| Runtime | Estágio | Spark | Delta | Java | Scala | Python | SO | Fim |
|---|---|---|---|---|---|---|---|---|
| 2.0 | GA | 4.1 (4.1.1) | 4.2 | 21 | 2.13.16 | 3.13 | Azure Linux 3.0 | EOS 2028-08-31 |
| 1.3 | EOSA | 3.5 (3.5.5) | 3.2 | 11 | 2.12.17 | 3.11 | Mariner 2.0 | EOS 2026-09-30; LTS de 2026-10-01 por 6 meses (até mar/2027) |

- Runtime 1.2 e 1.1 não aparecem mais na lista.
- Runtime 2.0 é GA mas **ainda não é o default**: o plano era virar default para novos
  workspaces/ambientes no fim de set/2026; a troca efetiva **não foi verificada**.
  Runtime 1.3 seguia default para novos workspaces na data da leitura.
- **Discrepância a vigiar:** 1.3 tem EOS 2026-09-30 e, ao mesmo tempo, LTS a partir de
  2026-10-01 — tratar como "suporte estendido LTS até mar/2027" conforme a página de lifecycle.
- Ciclo de vida: experimental preview 2–3 meses, preview 3 meses, GA 24 meses, LTS ~12
  meses, EOSA 6 meses antes do EOS.
- Matriz célula a célula: `knowledge/matrices/fabric-runtime.yaml`.

## Diferenças que quebram código ao migrar 1.3 → 2.0

- Spark 3.5 → 4.1, Scala 2.12 → 2.13, Java 11 → 21, Python 3.11 → 3.13: libs compiladas
  para Scala 2.12 não carregam.
- Features específicas do **Delta 4.2** no 2.0 são experimentais e **só Spark**: não usar
  em tabelas lidas por outros engines Fabric (SQL endpoint, Direct Lake).
- `EventHubConnector` está **deprecated** no 1.3: usar o conector Kafka do Spark
  (ver `azure.eventhubs.kafka-and-spark`).
- Custom live pools no 2.0: **PREVIEW**.

## Native Execution Engine

- Gluten + Velox, disponível em 1.3 e 2.0; ligado por `spark.native.enabled`.
- "Até 6x" em TPC-DS SF1000 é claim do fornecedor; não usar como estimativa.

## Lakehouse

- Duas pastas: **Tables** (Delta gerenciado, descoberta automática) e **Files**
  (qualquer formato).
- Arquivo Delta em Tables é validado, tem metadados extraídos e é registrado no metastore
  automaticamente.
- **SQL analytics endpoint** é **somente leitura** e só mostra tabelas **Delta**
  (incluindo shortcuts Delta).
- Lakehouse sem schema: metadados até 10 GB; acima disso usar lakehouse com schemas.
- Desde 2025-09-05 não há mais default semantic model criado automaticamente.
- Lakehouse × warehouse: lakehouse não tem transações multi-tabela; warehouse sim.

## Itens de execução

| Item | Uso |
|---|---|
| Notebook | Spark interativo (PySpark, Scala, SQL, R) |
| Spark job definition | aplicação compilada/script para ETL de produção |
| Pipeline (Data Factory) | orquestra notebooks/SJDs |
| Dataflow Gen2 | low-code |

## Consumo de capacidade

Spark consome CU da capacidade F; operações de background são suavizadas em 24 h.
Autoscale Billing for Spark tira o Spark de bursting/smoothing (ver
`azure.fabric.capacity-and-throttling`).

## Fatos que o Forge extrai

- Runtime declarado do ambiente/workspace; libs Scala 2.12 em ambiente 2.0.
- Uso de `EventHubConnector` (deprecated) em notebooks.
- Escrita em `Files/` de dados que deveriam ser tabela Delta (não aparecem no SQL endpoint).

## Não verificado

- Data efetiva em que o Runtime 2.0 passou a ser default.

## Fontes

- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0 (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3 (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview (retrieved: 2026-10-06)
