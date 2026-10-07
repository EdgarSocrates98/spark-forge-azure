---
name: azure-databricks
description: 'Use para jobs, clusters, cluster policies, DABs (databricks.yml) e notebooks do Azure Databricks:
  job falhando por config, DBR desatualizado, autoscale mal dimensionado, policy que bloqueia, Photon
  ligado/desligado, ''por que esse cluster custa tanto'', revisão de bundle. Analisa JSON exportado e
  código offline; coleta opcional e só leitura. Não decide grants do Unity Catalog nem custo final.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - databricks
  - cluster policy
  - databricks.yml
  - asset bundle
  - dbr
  - photon
  - job cluster
  - autoscale
  scope:
  - Azure Databricks
  - jobs
  - clusters
  - cluster policies
  - Databricks Asset Bundles
  - notebooks
  does:
  - lê cluster/job/policy JSON e DAB offline
  - detecta DBR fora de suporte, autoscale e node type inconsistentes
  - correlaciona notebook (# COMMAND) com o job que o executa
  does_not:
  - não decide grants/ownership de Unity Catalog (unity-catalog)
  - não cobre Fabric nem Synapse
  - não altera workspace (nunca cloud_write)
  knowledge_refs:
  - knowledge/azure/databricks/
  - knowledge/spark/
  tool_refs:
  - sparkforge-azure analyze databricks-job
  - sparkforge-azure analyze databricks-cluster
  - sparkforge-azure analyze dab
  - sparkforge-azure collect workspace-graph
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-databricks/evals/evals.yaml
  source_authority:
  - databricks_official
  - microsoft_official
---

# Azure Databricks

Plataforma de compute Databricks no Azure. Evidência vem de JSON exportado, DAB e notebooks — nunca de suposição sobre o workspace.

## Quando usar

- `databricks`
- `cluster policy`
- `databricks.yml`
- `asset bundle`
- `dbr`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — job JSON, cluster JSON, policy JSON, `databricks.yml` (DAB), notebooks `.py` com `# COMMAND ----------`. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze databricks-job --path exports/jobs/ --out .sparkforge-azure/facts.json
sparkforge-azure analyze databricks-cluster --path exports/clusters/
sparkforge-azure analyze dab --path databricks.yml
sparkforge-azure collect workspace-graph   # opt-in, read-only, exige credencial
```

   Fatos esperados:
   - `spark_version` (DBR) e status de suporte declarado no knowledge
   - autoscale min/max, node type, Photon, modo de acesso (dedicated/standard)
   - policy aplicada e atributos fixos/proibidos
   - tarefa → notebook/arquivo → cluster (job vs all-purpose)
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-databricks`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — conferir IDs (workspace ID, job ID, cluster ID) entre export e coleta; composição só por ID explícito, nunca por nome parecido.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Erro de permissão em tabela/volume → `unity-catalog` antes de mexer no cluster.
- Lentidão/OOM com event log → `spark-performance`.
- Pergunta de custo → `azure-finops` (aqui só fatos de configuração).
- All-purpose cluster executando job agendado → finding de configuração, custo fica com FinOps.

## Não concluir sem evidência

- Não afirmar economia ao trocar node type/Photon sem baseline medido.
- Não declarar o cluster "saudável" sem event log ou métricas.
- Não inferir modo de acesso UC pelo nome do cluster.
- Não supor que a policy está aplicada sem `policy_id` no JSON.

## Fronteiras

- Não decide grants/ownership de Unity Catalog (unity-catalog).
- Não cobre Fabric nem Synapse.
- Não altera workspace (nunca cloud_write).

## Handoff

- `unity-catalog` — erro de acesso a catálogo, schema, tabela, volume ou external location.
- `spark-performance` — sintoma de execução com event log.
- `azure-finops` — pergunta de custo ou DBU.
- `azure-terraform` — cluster/job declarado em Terraform.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
