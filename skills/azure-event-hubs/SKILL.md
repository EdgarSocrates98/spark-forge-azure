---
name: azure-event-hubs
description: 'Use para Event Hubs: namespace, hubs, partições, consumer groups, throughput/processing
  units, endpoint Kafka, Capture e opções Spark/Kafka de conexão. Sintomas: consumer lag, throttling (ServerBusy),
  poucas partições para o paralelismo, SASL mal configurado, consumer group compartilhado. Não decide
  semântica de streaming do Spark.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - event hubs
  - eventhub
  - consumer group
  - kafka endpoint
  - serverbusy
  - throughput unit
  - consumer lag
  scope:
  - Event Hubs
  - namespace
  - partições
  - consumer groups
  - Kafka endpoint
  - Capture
  does:
  - lê namespace/hub JSON (tier, TUs/PUs, partições, retenção)
  - lê opções Spark Kafka (bootstrap, SASL, startingOffsets)
  - detecta consumer group compartilhado entre consumidores
  does_not:
  - não decide semântica exactly-once/checkpoint do Spark (spark-streaming)
  - não cobre Eventstream do Fabric (fabric-realtime)
  - não altera namespace
  knowledge_refs:
  - knowledge/azure/eventhubs/
  tool_refs:
  - sparkforge-azure analyze pyspark
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze eventhubs-namespace
  - sparkforge-azure analyze spark-kafka-options
  eval_refs:
  - skills/azure-event-hubs/evals/evals.yaml
  source_authority:
  - microsoft_official
  - apache_spark_official
---

# Azure Event Hubs

Barramento de eventos. Capacidade e paralelismo vêm do namespace declarado; lag só com métrica.

## Quando usar

- `event hubs`
- `eventhub`
- `consumer group`
- `kafka endpoint`
- `serverbusy`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — namespace JSON (SKU, TU/PU, auto-inflate), hub JSON (partições, retenção, Capture), consumer groups, opções Kafka/Spark do consumidor. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze pyspark --path <repo> --out .sparkforge-azure/facts.json   # opções Kafka/Event Hubs no código
# Sem extrator de namespace ainda (planned_tool_refs): fatos de namespace (TU/PU,
# partições, consumer groups) completam o facts.json montados a mão do export.
```

   Fatos esperados:
   - tier e capacidade declarada
   - partições por hub vs paralelismo do consumidor
   - consumer group por aplicação
   - autenticação: SAS em código, Entra/MI, connection string em Key Vault
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-event-hubs`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — hub e consumer group citados existem no export; opção Kafka citada tem linha no código.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Pergunta de checkpoint/duplicidade no Spark → `spark-streaming`.
- Connection string em código → `azure-entra` (Key Vault/MI).
- Private endpoint/firewall no namespace → `azure-networking`.
- Throttling com métricas → `azure-observability` para correlação.

## Não concluir sem evidência

- Não afirmar ausência de lag sem métrica exportada.
- Não afirmar exactly-once a partir da configuração do Event Hubs.
- Não estimar TUs necessárias sem taxa de ingestão medida.
- Não expor connection strings; citar só local.

## Fronteiras

- Não decide semântica exactly-once/checkpoint do Spark (spark-streaming).
- Não cobre Eventstream do Fabric (fabric-realtime).
- Não altera namespace.

## Handoff

- `spark-streaming` — semântica do consumidor Spark.
- `fabric-realtime` — consumidor Eventstream.
- `azure-entra` — autenticação e segredos.
- `azure-observability` — métricas de throttling e lag.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
