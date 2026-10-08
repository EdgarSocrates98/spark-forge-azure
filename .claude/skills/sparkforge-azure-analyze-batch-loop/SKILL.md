---
name: sparkforge-azure-analyze-batch-loop
description: 'Use quando o job processa dados em lotes com for/while, collect de chaves, isin(list)
  gigante ou filtros por batch id, ou dispara action/write/count/merge dentro de loop, e você suspeita
  de recomputação do DAG, lineage crescente, múltiplos commits Delta/Iceberg ou OOM acumulado por
  iteração. Use também quando perguntarem "por que esse batch demora mais a cada lote" ou "o job cresce
  com o número de lotes". Rode `sparkforge-azure analyze pyspark` e filtre por `pyspark.loop` em vez
  de contar iterações e estimar custo de cabeça.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - batch
  - lote
  - loop
  - demora por lote
  - commits demais
  - o job cresce com o número de lotes
  scope:
  - loops for/while no PySpark
  - action/write/count/merge dentro de loop
  - collect de chaves + isin
  - lineage crescente por iteração
  does:
  - extrai facts pyspark.loop com profundidade e flags contains_action/contains_write
  - julga o lote contra SF-PY-004 sem depender de versão de runtime
  - separa o que o extrator marca do ponto cego real (loop sem action dentro)
  does_not:
  - não estima custo acumulado sem evidência (azure-finops decide custo)
  - não trata streaming (spark-streaming cobre microbatch/contínuo)
  - não executa o código analisado
  knowledge_refs:
  - knowledge/spark/
  tool_refs:
  - sparkforge-azure analyze pyspark
  - sparkforge-azure judge
  - sfa_analyze
  - sfa_judge
  eval_refs:
  - skills/analyze-batch-loop/evals/evals.yaml
  source_authority:
  - apache_spark_official
---
<!-- GENERATED from skills/analyze-batch-loop/SKILL.md; do not edit -->
# Analyze Batch Loop

## Procedimento

1. Extraia os facts:

```bash
sparkforge-azure analyze pyspark --path <arquivo-ou-diretório> --out .sparkforge-azure/facts.json --kind pyspark.loop
```

Cada `pyspark.loop` vem com `measures.loop_depth` (aninhamento) e
`attrs.contains_action`/`attrs.contains_write`.

2. Julgue:

```bash
sparkforge-azure judge --facts .sparkforge-azure/facts.json --show-skipped
```

Sem flag de versão: `SF-PY-004`, a regra que decide esta análise, é estrutural e não
declara `runtime_scope` — passar ou omitir a versão não muda se ela dispara. Os facts
vêm de `analyze pyspark`, que lê AST e nunca observa versão de runtime. Regras que
aparecem em `--show-skipped` com `reason: runtime_scope` são de outro domínio. `SF-PY-004`
(severidade `P0`) dispara quando `contains_action` ou `contains_write` é verdadeiro — o
padrão "reexecuta o DAG a montante a cada iteração" de `knowledge/spark/execution-model.md`.

3. Interprete o que o extrator não marca:

- Loop que só acumula DataFrames numa lista Python (`resultados.append(df_lote)`), sem
  action nem write dentro dele, **não gera** `pyspark.loop` — mesmo crescendo lineage a
  cada iteração. O sintoma aparece numa action única no fim, com plano gigante; procure
  `pyspark.chain` com `measures.length` alto perto do loop.
- `collect()` de chaves antes do loop aparece como `pyspark.driver_collect`, não como
  parte do `pyspark.loop` — correlacione pela proximidade de linha.
- `isin(lista_de_chaves)` não tem fact próprio; aparece dentro de `pyspark.chain`.
  Não assuma pruning só porque o filtro existe — confirme no plano físico.

## Pontos de decisão

> O batch reduz o scan e o shuffle desde a origem, ou o Spark recompõe o pipeline caro a
> cada action?

- Escrever tudo numa única action, com `partitionBy` pela coluna de lote quando o objetivo
  é separar a saída.
- Se o loop é inevitável, materializar o DataFrame caro uma vez antes (tabela intermediária
  ou checkpoint).
- Reduzir na origem, com filtro que chegue ao pushdown, em vez de filtrar um DAG caro.
- Trocar `collect` de chaves + `isin(list)` por join distribuído contra tabela de chaves.

## Não concluir sem evidência

- Sem `pyspark.loop` no facts.json, não declare "recomputação por iteração" — registre o
  padrão como `unresolved`: não foi observado, o que não prova que não existe (o ponto
  cego acima é real).
- `contains_action`/`contains_write` falsos nos dois lados: o loop existe mas ainda não é
  prova de recomputação; correlacione com o event log antes de afirmar custo.
- Nunca reporte "N× mais lento" sem baseline medido do mesmo caso.

## Handoff

- `azure-finops` — custo do padrão em termos de DBU/capacity.
- `spark-streaming` — loop dentro de streaming (foreachBatch, micro-batch).
- `spark-performance` — skew/spill no stage que o loop produz.
