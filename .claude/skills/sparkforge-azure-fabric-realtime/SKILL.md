---
name: sparkforge-azure-fabric-realtime
description: 'Use para Real-Time Intelligence do Fabric: Eventstream, Eventhouse/KQL Database, Activator
  e ingestão a partir de Event Hubs. Sintomas: eventos atrasando no Eventstream, tabela KQL sem dados,
  política de retenção/caching, destino Lakehouse do Eventstream. Não cobre Spark Structured Streaming
  nem configuração do namespace Event Hubs.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - eventstream
  - eventhouse
  - kql database
  - real-time intelligence
  - activator
  - rti
  scope:
  - Fabric Real-Time Intelligence
  - Eventstream
  - Eventhouse
  - KQL Database
  - Activator
  does:
  - lê definição de Eventstream (fontes, transformações, destinos)
  - verifica retenção/caching declarados no Eventhouse
  - liga fonte Event Hubs ao consumer group usado
  does_not:
  - não cobre Spark Structured Streaming (spark-streaming)
  - não configura namespace/partições Event Hubs (azure-event-hubs)
  - não cobre Azure Data Explorer fora do Fabric
  knowledge_refs:
  - knowledge/azure/fabric/
  - knowledge/azure/eventhubs/
  tool_refs:
  - sparkforge-azure analyze fabric-eventstream
  - sparkforge-azure analyze fabric-item
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/fabric-realtime/evals/evals.yaml
  source_authority:
  - microsoft_official
---
<!-- GENERATED from skills/fabric-realtime/SKILL.md; do not edit -->
# Fabric Real-Time Intelligence

Ingestão e análise em tempo real no Fabric. Latência e completude só são afirmadas com métricas exportadas.

## Quando usar

- `eventstream`
- `eventhouse`
- `kql database`
- `real-time intelligence`
- `activator`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — definição de Eventstream, políticas do Eventhouse/KQL DB (retention, caching, ingestion batching), fonte Event Hubs (namespace, hub, consumer group). Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze fabric-eventstream --path fabric-workspace/eventstreams/ --out .sparkforge-azure/facts.json
sparkforge-azure analyze fabric-item --path fabric-workspace/
```

   Fatos esperados:
   - fonte → transformações → destinos do Eventstream
   - consumer group por consumidor (compartilhamento é risco)
   - retenção e caching do KQL DB
   - destino Lakehouse e formato
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain fabric-realtime`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — consumer group e hub conferidos contra o export do Event Hubs; sem export, `unresolved`.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Consumer group compartilhado com outro consumidor → finding, handoff `azure-event-hubs`.
- Pergunta sobre Spark lendo o mesmo hub → `spark-streaming`.
- Custo de capacidade → `azure-finops`.
- Dados ausentes na tabela → verificar política de ingestão antes de culpar a fonte.

## Não concluir sem evidência

- Não afirmar "sem perda de dados" sem reconciliação de contagem fonte×destino.
- Não afirmar latência fim-a-fim sem métrica exportada.
- Não afirmar exactly-once para Eventstream.
- Não tratar KQL DB do Fabric como cluster ADX standalone.

## Fronteiras

- Não cobre Spark Structured Streaming (spark-streaming).
- Não configura namespace/partições Event Hubs (azure-event-hubs).
- Não cobre Azure Data Explorer fora do Fabric.

## Handoff

- `azure-event-hubs` — namespace, partições, consumer groups, throughput.
- `spark-streaming` — consumidor Spark do mesmo fluxo.
- `azure-finops` — capacidade/custo.
- `azure-observability` — métricas e alertas.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
