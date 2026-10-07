---
name: sparkforge-azure-azure-observability
description: 'Use para Azure Monitor, Log Analytics (KQL), diagnostic settings, alertas, system tables
  do Databricks e monitoring do Fabric. Sintomas: ''não temos logs do job'', diagnostic settings faltando,
  alerta que nunca dispara, falhas intermitentes sem correlação, ''o pipeline está saudável?''. Lê exports
  e configurações; nunca declara saúde sem métrica.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - azure monitor
  - log analytics
  - kql
  - diagnostic settings
  - alerta
  - system tables
  - observabilidade
  - logs do job
  scope:
  - Azure Monitor
  - Log Analytics
  - diagnostic settings
  - alertas
  - Databricks system tables
  - Fabric monitoring
  does:
  - verifica cobertura de diagnostic settings por recurso
  - lê exports de Log Analytics/system tables para correlação
  - avalia regras de alerta declaradas (sinal, limiar, ação)
  does_not:
  - não declara recurso "saudável"
  - não substitui Azure Monitor
  - não decide custo (azure-finops)
  knowledge_refs:
  - knowledge/azure/observability/
  tool_refs:
  - sparkforge-azure analyze diagnostic-settings
  - sparkforge-azure analyze log-analytics-export
  - sparkforge-azure collect workspace-graph
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-observability/evals/evals.yaml
  source_authority:
  - microsoft_official
  - databricks_official
---
<!-- GENERATED from skills/azure-observability/SKILL.md; do not edit -->
# Observabilidade Azure Data

Observabilidade é cobertura de sinal + evidência. Ausência de alerta não é ausência de problema.

## Quando usar

- `azure monitor`
- `log analytics`
- `kql`
- `diagnostic settings`
- `alerta`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — diagnostic settings por recurso, export de consultas KQL (com janela de tempo), export de system tables (`system.lakeflow`, `system.compute`), regras de alerta. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze diagnostic-settings --path exports/diagnostics/ --out .sparkforge-azure/facts.json
sparkforge-azure analyze log-analytics-export --path exports/kql/
sparkforge-azure collect workspace-graph   # opt-in, read-only
```

   Fatos esperados:
   - recursos sem diagnostic setting ou sem categorias relevantes
   - destino (workspace Log Analytics, storage, Event Hubs) e retenção
   - falhas por job/pipeline na janela exportada
   - alertas: sinal, limiar, frequência, action group
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-observability`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — toda contagem cita a janela de tempo e a consulta/export de origem.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Falhas de job com causa de execução → `spark-performance`/`azure-databricks`.
- Custo de ingestão de logs → `azure-finops`.
- Falha de pipeline ADF → `azure-data-factory`.
- Recurso sem diagnostic setting → finding de cobertura.

## Não concluir sem evidência

- Nunca declarar "saudável" ou "sem incidentes" sem métrica na janela.
- Não afirmar que um alerta funciona sem histórico de disparo ou teste.
- Não extrapolar janela curta como tendência.
- Não comparar métricas de janelas diferentes sem declarar.

## Fronteiras

- Não declara recurso "saudável".
- Não substitui Azure Monitor.
- Não decide custo (azure-finops).

## Handoff

- `azure-finops` — custo de ingestão e retenção.
- `spark-performance` — falhas/lentidão de Spark.
- `azure-data-factory` — falhas de pipeline.
- `azure-databricks` — system tables de jobs/clusters.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
