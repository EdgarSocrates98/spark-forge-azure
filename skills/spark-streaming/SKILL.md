---
name: spark-streaming
description: 'Use para Spark Structured Streaming em Databricks/Fabric/Synapse: readStream/writeStream,
  checkpoint, watermark, triggers (availableNow, processingTime), foreachBatch, fontes Event Hubs/Kafka/Auto
  Loader e sinks Delta. Sintomas: duplicidade após restart, checkpoint compartilhado, estado crescendo,
  atraso crescente, ''é exactly-once?''. Nunca afirma exactly-once sem evidência.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - structured streaming
  - readstream
  - writestream
  - checkpoint
  - watermark
  - foreachbatch
  - availablenow
  - exactly-once
  - auto loader
  scope:
  - Structured Streaming
  - checkpoints
  - watermarks
  - triggers
  - foreachBatch
  - Auto Loader
  - sinks Delta
  does:
  - extrai fontes, sinks, checkpoints e triggers do código
  - detecta checkpoint compartilhado e foreachBatch não idempotente
  - verifica watermark vs estado com agregação
  does_not:
  - não configura Event Hubs (azure-event-hubs)
  - não cobre Eventstream do Fabric (fabric-realtime)
  - não afirma garantias de entrega sem evidência
  knowledge_refs:
  - knowledge/spark/
  - knowledge/azure/eventhubs/
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
  - sparkforge-azure analyze streaming
  eval_refs:
  - skills/spark-streaming/evals/evals.yaml
  source_authority:
  - apache_spark_official
  - databricks_official
  - microsoft_official
---

# Spark Structured Streaming

Streaming tem garantias condicionais: dependem de fonte replayable, checkpoint exclusivo e sink idempotente — todos provados.

## Quando usar

- `structured streaming`
- `readstream`
- `writestream`
- `checkpoint`
- `watermark`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — código com `readStream`/`writeStream`, localização de checkpoints, opções da fonte (Kafka/Event Hubs/Auto Loader), sink e propriedades da tabela. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze pyspark --path <repo> --out .sparkforge-azure/facts.json   # readStream/writeStream no código
sparkforge-azure lab run cdc-duplicate-restart   # duplicidade pós-restart (cenário mais próximo), opcional
sparkforge-azure lab verify
```

   Fatos esperados:
   - query → fonte → sink → checkpoint (caminho)
   - checkpoints reutilizados por mais de uma query
   - watermark e operadores com estado
   - foreachBatch: escrita idempotente (MERGE por chave, txnVersion) ou append cego
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain spark-streaming`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — cenário de restart reproduzido no Forge Lab; garantia só é dita com o nome do caso que passou.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- foreachBatch com append sem chave → finding de duplicidade em restart.
- Fonte Event Hubs com consumer group compartilhado → `azure-event-hubs`.
- Sink Delta com small files → `delta-lake`.
- Estado crescendo sem watermark → finding de memória/estado.

## Não concluir sem evidência

- Nunca afirmar exactly-once sem fonte replayable, checkpoint exclusivo e sink idempotente provados.
- Não afirmar "sem perda de dados" sem reconciliação fonte×sink.
- Não declarar o stream "saudável" sem métricas de progresso.
- Dizer "casos declarados passaram no lab", não "garantido".

## Fronteiras

- Não configura Event Hubs (azure-event-hubs).
- Não cobre Eventstream do Fabric (fabric-realtime).
- Não afirma garantias de entrega sem evidência.

## Handoff

- `azure-event-hubs` — fonte Event Hubs/Kafka.
- `delta-lake` — sink Delta.
- `spark-performance` — micro-batch lento com event log.
- `fabric-realtime` — pipeline equivalente em Eventstream.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
