---
name: spark-performance
description: 'Use quando um job Spark está lento, estoura memória ou custa demais e há evidência de execução:
  event log, plano físico (EXPLAIN), Spark UI exportada, métricas de stage. Sintomas: skew, spill, OOM
  no executor ou driver, shuffle gigante, AQE desligado, broadcast falhando, small files na leitura, ''por
  que esse stage demora?''. Mede antes de propor; propõe com teste no Forge Lab.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - job lento
  - skew
  - oom
  - spill
  - shuffle
  - aqe
  - broadcast
  - event log
  - stage demora
  - out of memory
  scope:
  - event log
  - plano físico
  - stages
  - tasks
  - AQE
  - joins
  - shuffle
  - memória
  does:
  - extrai métricas de stage/task do event log
  - detecta skew, spill e shuffle dominante com números
  - valida hipótese no Forge Lab antes de recomendar
  does_not:
  - não cobre semântica de streaming (spark-streaming)
  - não promete economia (azure-finops decide custo)
  - não roda no cluster do usuário
  knowledge_refs:
  - knowledge/spark/
  tool_refs:
  - sparkforge-azure analyze pyspark
  - sparkforge-azure lab run
  - sparkforge-azure lab verify
  - sfa_analyze
  - sfa_lab_run
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze spark-eventlog
  eval_refs:
  - skills/spark-performance/evals/evals.yaml
  source_authority:
  - apache_spark_official
  - databricks_official
  - microsoft_official
---

# Spark Performance

Desempenho é medido, não adivinhado. Sem event log ou plano, o resultado é hipótese marcada como tal.

## Quando usar

- `job lento`
- `skew`
- `oom`
- `spill`
- `shuffle`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — event log Spark (JSON), `EXPLAIN FORMATTED`, spark.conf efetivo, código PySpark do job. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze pyspark --path <repo> --out .sparkforge-azure/facts.json
sparkforge-azure lab run spark-skew   # digital twin determinístico, opcional
sparkforge-azure lab verify
# Sem extrator de event log ainda (planned_tool_refs): fatos de stage/task/skew/
# spill completam o facts.json montados a mão do eventlog exportado.
```

   Fatos esperados:
   - duração por stage e stage dominante
   - distribuição de tamanho/tempo de task (p50/p99/max) para skew
   - spill memória/disco e shuffle read/write
   - AQE, broadcast threshold e partições de shuffle efetivas
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain spark-performance`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — hipótese reproduzida no Forge Lab (`lab verify`) antes de virar recomendação; sem reprodução, fica `unresolved`.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Sem event log → produzir só hipóteses estruturais do código e pedir o artefato.
- Skew confirmado (p99 ≫ p50 na mesma stage) → avaliar AQE skew join/salting.
- Leitura dominada por small files → `delta-lake`.
- Pergunta de custo → `azure-finops` com as métricas daqui.

## Não concluir sem evidência

- Não afirmar ganho percentual sem medição antes/depois.
- Não declarar o job "otimizado" ou "saudável".
- Não atribuir causa única sem stage dominante identificada.
- Não recomendar aumentar memória sem evidência de spill/OOM.

## Fronteiras

- Não cobre semântica de streaming (spark-streaming).
- Não promete economia (azure-finops decide custo).
- Não roda no cluster do usuário.

## Handoff

- `delta-lake` — layout de arquivos e MERGE.
- `azure-finops` — custo.
- `spark-streaming` — jobs de streaming.
- `azure-databricks` — configuração de cluster.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
