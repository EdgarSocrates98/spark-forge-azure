---
name: sparkforge-azure-azure-spark
description: 'Use quando houver código PySpark/Spark SQL ou spark.conf rodando em Azure (Databricks, Fabric
  ou Synapse) e a pergunta for de correção, padrões caros ou portabilidade entre runtimes: collect() em
  dado grande, UDF Python, cache sem unpersist, conf divergente entre ambientes, ''esse job roda igual
  no Fabric?''. Ponto de entrada genérico antes de skills de plataforma; extrai facts por AST sem executar
  código.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - pyspark
  - spark sql
  - spark.conf
  - collect()
  - udf
  - roda igual no fabric
  - portar job spark
  scope:
  - PySpark
  - Spark SQL
  - spark.conf
  - Databricks Runtime
  - Fabric Spark
  - Synapse Spark
  does:
  - extrai facts de código PySpark por AST sem executar
  - compara spark.conf declarado entre runtimes Azure
  - aponta padrões caros com evidência de linha
  does_not:
  - não faz tuning profundo por event log (spark-performance)
  - não cobre semântica de streaming (spark-streaming)
  - não executa o código analisado
  knowledge_refs:
  - knowledge/spark/
  tool_refs:
  - sparkforge-azure analyze pyspark
  - sparkforge-azure tokensave search
  - sfa_analyze
  - sfa_tokensave_search
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze spark-conf
  eval_refs:
  - skills/azure-spark/evals/evals.yaml
  source_authority:
  - apache_spark_official
  - microsoft_official
  - databricks_official
---
<!-- GENERATED from skills/azure-spark/SKILL.md; do not edit -->
# Azure Spark (genérico)

Ponto de entrada para código Spark em qualquer runtime Azure. Trata o código como dado: AST, nunca execução.

## Quando usar

- `pyspark`
- `spark sql`
- `spark.conf`
- `collect()`
- `udf`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — código PySpark/Spark SQL do repositório, `spark.conf` declarado (cluster JSON, environment do Fabric, pool do Synapse). Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze pyspark --path <repo> --out .sparkforge-azure/facts.json
sparkforge-azure tokensave search "collect(" --root <repo>
# spark.conf efetivo ainda sem extrator (planned_tool_refs): fatos de config
# completam o facts.json montados a mão do dump de conf.
```

   Fatos esperados:
   - actions em driver (`collect`, `toPandas`) com linha e tamanho declarado do input
   - UDF Python vs função nativa equivalente
   - `cache`/`persist` sem `unpersist` correspondente
   - chaves de `spark.conf` que diferem entre runtimes
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-spark`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — reabrir a linha citada com `tokensave read`; confirmar que o runtime alvo é o declarado no artefato, não o presumido.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Runtime declarado é Databricks → handoff para `azure-databricks`; Fabric → `fabric-data-engineering`; Synapse → `azure-synapse`.
- Sintoma é lentidão com event log disponível → `spark-performance`.
- Código usa `readStream`/`writeStream` → `spark-streaming`.
- Conf presente só em um ambiente → registrar divergência como fact, não como bug.

## Não concluir sem evidência

- Não afirmar que o job "roda igual" em outro runtime sem comparar conf e versão de Spark declaradas.
- Não estimar duração ou custo a partir do código estático.
- Não afirmar que UDF é a causa de lentidão sem evidência de execução (event log/plano).
- Não concluir sobre dados de produção a partir de amostra local.

## Fronteiras

- Não faz tuning profundo por event log (spark-performance).
- Não cobre semântica de streaming (spark-streaming).
- Não executa o código analisado.

## Handoff

- `spark-performance` — há event log, plano físico ou sintoma de lentidão/OOM.
- `azure-databricks` — runtime declarado é Databricks.
- `fabric-data-engineering` — runtime declarado é Fabric.
- `azure-synapse` — runtime declarado é Synapse Spark pool.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
