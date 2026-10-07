---
name: azure-finops
description: 'Use para custo de Databricks, Fabric, Synapse e storage: export do Cost Management, system.billing.usage,
  capacity metrics do Fabric, DBU por job/cluster, tags de chargeback, reservas. Sintomas: ''por que a
  conta subiu?'', job que custa demais, capacidade Fabric em throttling, custo sem atribuição. Nunca promete
  economia sem baseline medido.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - custo
  - cost
  - finops
  - dbu
  - billing
  - capacity units
  - chargeback
  - conta subiu
  - reservation
  scope:
  - Cost Management
  - system.billing.usage
  - Fabric capacity
  - DBU
  - tags
  - reservas
  does:
  - correlaciona compute × duração × configuração × storage × rede
  - atribui custo por tag/job/workspace com cobertura explícita
  - separa custo medido de estimativa
  does_not:
  - não promete economia sem baseline
  - não altera SKU, reserva ou cluster
  - não substitui o Cost Management
  knowledge_refs:
  - knowledge/azure/finops/
  tool_refs:
  - sparkforge-azure analyze cost-export
  - sparkforge-azure analyze billing-usage
  - sparkforge-azure collect workspace-graph
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-finops/evals/evals.yaml
  source_authority:
  - microsoft_official
  - databricks_official
  - finops_foundation
---

# FinOps Azure Data

Custo é fato medido com período, moeda e cobertura. Recomendação sem baseline é hipótese, não economia.

## Quando usar

- `custo`
- `cost`
- `finops`
- `dbu`
- `billing`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — export CSV do Cost Management (período, moeda), `system.billing.usage` exportado, capacity metrics do Fabric, tags dos recursos. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze cost-export --path exports/cost/ --out .sparkforge-azure/facts.json
sparkforge-azure analyze billing-usage --path exports/system_billing_usage/
sparkforge-azure collect workspace-graph   # opt-in, read-only, para tags
```

   Fatos esperados:
   - custo por recurso/serviço/tag no período, com moeda
   - DBU por SKU, job e cluster
   - percentual de custo sem tag (cobertura de atribuição)
   - uso de CU e eventos de throttling da capacidade Fabric
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-finops`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — somatório por dimensão bate com o total do export; período e moeda declarados em toda cifra.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Custo concentrado em all-purpose cluster → `azure-databricks` para fatos de config.
- Job caro e lento → `spark-performance` antes de propor redução.
- Throttling Fabric → `fabric-data-engineering` para workloads da capacidade.
- Cobertura de tag baixa → finding de governança de custo.

## Não concluir sem evidência

- Nunca afirmar "X% de economia" sem baseline e medição pós-mudança.
- Não comparar períodos com moeda ou cobertura diferentes.
- Não atribuir custo a time sem tag ou mapeamento explícito.
- Não extrapolar preço de tabela como custo real.

## Fronteiras

- Não promete economia sem baseline.
- Não altera SKU, reserva ou cluster.
- Não substitui o Cost Management.

## Handoff

- `azure-databricks` — configuração de cluster/job.
- `spark-performance` — eficiência de execução.
- `fabric-data-engineering` — workloads na capacidade Fabric.
- `cost-reviewer` — revisão de proposta de redução.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
