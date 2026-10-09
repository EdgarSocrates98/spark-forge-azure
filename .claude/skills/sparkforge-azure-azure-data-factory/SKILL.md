---
name: sparkforge-azure-azure-data-factory
description: 'Use para Azure Data Factory: pipelines, activities, linked services, datasets, triggers
  e integration runtimes (Azure, self-hosted, managed VNet) a partir do ARM export. Sintomas: copy activity
  lenta, SHIR offline, linked service com segredo inline, trigger duplicado, ''qual pipeline quebra se
  eu mudar este dataset?''. Data Factory do Fabric não é ADF.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - data factory
  - adf
  - integration runtime
  - self-hosted integration runtime
  - linked service
  - copy activity
  - trigger adf
  scope:
  - Azure Data Factory
  - pipelines
  - linked services
  - datasets
  - triggers
  - integration runtimes
  does:
  - lê ARM export do ADF offline
  - detecta segredo inline vs Key Vault reference
  - calcula impacto de mudança via grafo pipeline↔dataset↔linked service
  does_not:
  - não cobre Data Factory do Fabric (fabric-data-engineering)
  - não executa pipelines
  - não diagnostica rede do SHIR sozinho (azure-networking)
  knowledge_refs:
  - knowledge/azure/adf/
  tool_refs:
  - sparkforge-azure graph build
  - sparkforge-azure graph impact
  - sfa_analyze
  - sfa_graph_impact
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze adf-pipeline
  eval_refs:
  - skills/azure-data-factory/evals/evals.yaml
  source_authority:
  - microsoft_official
---
<!-- GENERATED from skills/azure-data-factory/SKILL.md; do not edit -->
# Azure Data Factory

Orquestração ADF lida como dado (ARM JSON). O grafo de dependências é a principal evidência de impacto.

## Quando usar

- `data factory`
- `adf`
- `integration runtime`
- `self-hosted integration runtime`
- `linked service`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — ARM export da factory (pipelines, datasets, linked services, triggers, integration runtimes), histórico de runs exportado quando houver. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure graph build --root adf-arm-export/
sparkforge-azure graph impact --graph .sparkforge-azure/graph/graph.json --changed adf-arm-export/<pipeline>.json
# Sem extrator de pipeline ainda (planned_tool_refs): fatos de pipelines/datasets/
# triggers entram em .sparkforge-azure/facts.json montados a mão do ARM export.
```

   Fatos esperados:
   - pipeline → activities → dataset → linked service → IR
   - credenciais: Key Vault reference, managed identity ou segredo inline
   - triggers e janelas (schedule, tumbling window, event)
   - IR self-hosted vs managed VNet
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-data-factory`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — todo nó do grafo tem origem no export; nó citado sem arquivo vira `unresolved`.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Segredo inline em linked service → finding de segurança, handoff `azure-entra` para Key Vault/MI.
- SHIR sem conectividade → `azure-networking`.
- Artefato com `Microsoft.Fabric`/item de workspace Fabric → `fabric-data-engineering`.
- Copy lenta com métricas de run → analisar DIU/paralelismo declarados antes de concluir.

## Não concluir sem evidência

- Não aplicar regra de ADF a pipeline do Fabric.
- Não afirmar impacto "zero" de mudança sem grafo completo.
- Não afirmar throughput de copy sem métricas de run.
- Não expor valores de segredo encontrados; citar só o caminho JSON.

## Fronteiras

- Não cobre Data Factory do Fabric (fabric-data-engineering).
- Não executa pipelines.
- Não diagnostica rede do SHIR sozinho (azure-networking).

## Handoff

- `azure-entra` — credenciais, managed identity, Key Vault.
- `azure-networking` — SHIR, managed VNet, private endpoints.
- `fabric-data-engineering` — pipeline do Fabric.
- `azure-observability` — métricas e alertas de runs.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
