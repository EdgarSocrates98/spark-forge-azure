---
id: data-quality.contracts-and-expectations
title: Qualidade de dados - contratos, expectations e monitoramento no Azure
domain: data-quality
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/ldp/expectations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/purview/unified-catalog
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/features/change-data-feed
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.databricks.workflows, lakehouse.delta-lake, azure.purview.unified-catalog-and-lineage, agentic.evidence-first]
---

# Qualidade de dados — contratos e expectations

## Contrato de dados (conceito interno do Forge)

Um contrato declara, por dataset: schema (nomes, tipos, nulabilidade), chaves, regras de
valor, frescor esperado, volume esperado e dono. O Forge trata contrato como **fato
declarado** e compara com **fatos observados** (schema real, contagens, métricas de
expectations). Divergência vira achado com as duas evidências.

## Expectations em Lakeflow pipelines (Databricks)

| Ação | SQL | Python | Efeito |
|---|---|---|---|
| warn (default) | `CONSTRAINT n EXPECT (expr)` | `@dp.expect` | registro inválido é gravado; métrica coletada |
| drop | `... ON VIOLATION DROP ROW` | `@dp.expect_or_drop` | inválido descartado; contagem logada |
| fail | `... ON VIOLATION FAIL UPDATE` | `@dp.expect_or_fail` | update falha; transação revertida; **sem métricas** |

- Grupo: `expect_all`, `expect_all_or_drop`, `expect_all_or_fail` (só Python).
- Restrições da expressão: SQL booleano válido; **sem** funções Python customizadas,
  chamadas externas ou subqueries a outras tabelas.
- Nome de expectation único por dataset.
- Métricas: aba Data quality do pipeline ou **event log** do pipeline.
- Em pipeline triggered, falha de um flow não derruba flows paralelos; em contínuo, para o
  flow e dependentes.
- Erro documentado de violação: `[EXPECTATION_VIOLATION.VERBOSITY_ALL] Flow '...' failed
  to meet the expectation.` com input/output do registro.
- Sem métricas quando: não há expectations, operador sem suporte, sinks, nenhum update no
  run, ou `pipelines.metrics.flowTimeReporter.enabled` ausente.
- Expectations **não** suportadas com `AUTO CDC FROM SNAPSHOT`.
- Padrão quarentena: rotear inválidos para outra tabela em vez de drop/fail.

## Monitoramento gerenciado

- `system.data_quality_monitoring.table_results` (**Public Preview**): checagens de
  frescor e completude e incidentes, retenção 13 meses.
- `system.data_classification.results` (**Public Preview**): classes de dados sensíveis.
- Purview Unified Catalog inclui módulo de **data quality** e critical data elements.

## Regras do Forge

- Expectation `warn` em camada servida a consumo (gold) sem alerta: achado de risco.
- `fail` sem quarentena em pipeline contínuo: risco de parada total.
- Contrato sem dono ou sem frescor declarado: incompleto (`unresolved`, não "ok").
- Métrica ausente ≠ zero violações.

## Não verificado

- Ferramentas OSS (Great Expectations, Soda, DQX) não foram verificadas nesta base.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/ldp/expectations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/purview/unified-catalog (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/features/change-data-feed (retrieved: 2026-10-06)
