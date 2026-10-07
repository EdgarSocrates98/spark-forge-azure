---
name: delta-lake
description: 'Use para tabelas Delta: _delta_log, MERGE lento ou regressivo, small files, OPTIMIZE/Z-ORDER/liquid
  clustering, VACUUM e retenção, deletion vectors, change data feed, time travel, conflitos de escrita
  concorrente. Sintomas: ''MERGE ficou lento'', ''muitos arquivos pequenos'', ''VACUUM apagou o que eu
  precisava'', ConcurrentAppendException. Lê o log, nunca reescreve a tabela.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - delta
  - _delta_log
  - merge lento
  - small files
  - optimize
  - vacuum
  - liquid clustering
  - deletion vectors
  - concurrentappendexception
  scope:
  - Delta Lake
  - _delta_log
  - MERGE
  - OPTIMIZE
  - VACUUM
  - liquid clustering
  - change data feed
  does:
  - lê commits do _delta_log (operação, métricas, arquivos)
  - mede distribuição de tamanho de arquivo e crescimento por commit
  - verifica propriedades de tabela (retenção, DV, CDF, clustering)
  does_not:
  - não executa OPTIMIZE/VACUUM/MERGE
  - não cobre Iceberg (iceberg) além de UniForm declarado
  - não faz tuning de Spark fora da tabela (spark-performance)
  knowledge_refs:
  - knowledge/lakehouse/
  tool_refs:
  - sparkforge-azure analyze delta-log
  - sparkforge-azure lab run
  - sfa_analyze
  - sfa_lab_run
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/delta-lake/evals/evals.yaml
  source_authority:
  - delta_io_official
  - databricks_official
---

# Delta Lake

Formato de tabela. O `_delta_log` é a evidência primária: cada afirmação cita versão e operação.

## Quando usar

- `delta`
- `_delta_log`
- `merge lento`
- `small files`
- `optimize`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — diretório `_delta_log/` (JSON + checkpoints), `DESCRIBE DETAIL`/`DESCRIBE HISTORY` exportados, propriedades da tabela. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze delta-log --path <tabela>/_delta_log --out .sparkforge-azure/facts.json
sparkforge-azure lab run delta-merge-small-files   # digital twin determinístico, opcional
```

   Fatos esperados:
   - operações por versão (WRITE, MERGE, OPTIMIZE, VACUUM) e métricas (numFiles, bytes)
   - tamanho médio/mediano de arquivo e tendência
   - propriedades: `delta.deletedFileRetentionDuration`, DV, CDF, clustering
   - conflitos e reescritas por MERGE (numTargetFilesRemoved)
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain delta-lake`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — versão citada existe no log; métrica citada vem de `operationMetrics`, não de estimativa.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- MERGE reescrevendo muitos arquivos → avaliar predicado/clustering antes de sugerir OPTIMIZE.
- Small files por streaming → `spark-streaming` (trigger/foreachBatch).
- Leitura lenta com plano/event log → `spark-performance`.
- Tabela com UniForm/Iceberg → `iceberg` para o lado de metadados Iceberg.

## Não concluir sem evidência

- Não afirmar que VACUUM é seguro sem comparar retenção com time travel e streams leitores.
- Não afirmar ganho de OPTIMIZE sem medir antes/depois.
- Não afirmar "sem perda de dados" após VACUUM.
- Não inferir tamanho de tabela sem `DESCRIBE DETAIL` ou log.

## Fronteiras

- Não executa OPTIMIZE/VACUUM/MERGE.
- Não cobre Iceberg (iceberg) além de UniForm declarado.
- Não faz tuning de Spark fora da tabela (spark-performance).

## Handoff

- `spark-performance` — plano físico e execução.
- `spark-streaming` — escrita streaming gerando small files.
- `iceberg` — UniForm/metadados Iceberg.
- `unity-catalog` — tabela gerenciada e permissões.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
