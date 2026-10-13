# Receita — Streaming: Event Hubs e Fabric RTI

**O quê:** `sparkforge-azure diagnose stream --bundle <case>` cobre Event
Hubs (namespace, partições, consumer groups, TU/PU, Capture), checkpoints e
Structured Streaming, mais Real-Time Intelligence do Fabric (Eventstream,
Eventhouse/KQL, Activator).
**Por que:** "é exactly-once?" e "por que o lag cresce" se respondem com
evidência de checkpoint/consumer group — nunca por declaração.
**Quando:** consumer lag, throttling (ServerBusy), checkpoint compartilhado,
duplicidade após restart, Eventstream atrasando.
**Quando não:** configuração do namespace Event Hubs em si sem bundle —
é `azure-event-hubs` (skill), não o diagnose.

## Passo a passo

```bash
sparkforge-azure diagnose stream --bundle <dir-do-case>
sparkforge-azure diagnose stream --suite tests/fixtures/stream           # 22 cenários
sparkforge-azure diagnose stream --suite tests/fixtures/stream --profile deep
```

O bundle junta exports do namespace/hubs + artefatos de checkpoint +
progresso do stream. Fabric RTI entra com Eventstream/Eventhouse no mesmo
case quando o pipeline mistura transporte + destino.

## Interpretação

`failure_layer` separa transporte (Event Hubs) de processamento
(checkpoint/state do Spark) de destino (RTI). A saída nunca afirma
exactly-once sem evidência de idempotência/checkpoint — duplicidade
suspeita fica `unresolved` se a prova não veio no bundle.

## Verificação

22 cenários com `expect:` — cobrem consumer group compartilhado, partições
insuficientes para o paralelismo e SASL mal configurado.

## Limitações

Semântica de exactly-once exige evidência dos dois lados; bundle sem o
checkpoint do sink fica `unresolved` por honestidade.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| lag crescente | poucas partições p/ o paralelismo ou consumer group compartilhado | export do namespace + progresso no bundle |
| duplicidade pós-restart | checkpoint compartilhado/estado crescendo | `diagnose stream` aponta a camada; decisão de exactly-once exige prova |
