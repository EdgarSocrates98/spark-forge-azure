---
name: iceberg
description: 'Use para tabelas Apache Iceberg em Azure (Databricks UniForm, catálogo REST, OneLake): metadata.json,
  snapshots, manifest lists, expiração de snapshots, evolução de partição/esquema, compactação. Sintomas:
  muitos snapshots, metadata crescendo, leitor externo sem ver dados novos, UniForm desatualizado. Catálogos
  AWS (Glue, Lake Formation) não são equivalentes.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - iceberg
  - uniform
  - metadata.json
  - snapshot
  - manifest list
  - expire snapshots
  - iceberg rest catalog
  scope:
  - Apache Iceberg
  - UniForm
  - snapshots
  - manifests
  - catálogo REST
  - evolução de partição
  does:
  - lê metadata.json, snapshots e manifest lists
  - mede crescimento de snapshots e manifests
  - verifica sincronização UniForm declarada
  does_not:
  - não trata Glue/Lake Formation como catálogo Azure
  - não executa expire_snapshots/rewrite_data_files
  - não cobre o log Delta (delta-lake)
  knowledge_refs:
  - knowledge/lakehouse/
  tool_refs:
  - sparkforge-azure analyze iceberg-metadata
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/iceberg/evals/evals.yaml
  source_authority:
  - apache_iceberg_official
  - databricks_official
  - microsoft_official
---

# Apache Iceberg

Formato de tabela aberto. Metadados Iceberg são a evidência; catálogo e leitor são declarados, nunca presumidos.

## Quando usar

- `iceberg`
- `uniform`
- `metadata.json`
- `snapshot`
- `manifest list`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — `metadata/*.metadata.json`, manifest lists e manifests, propriedades da tabela, config do catálogo (REST/UC), estado UniForm. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze iceberg-metadata --path <tabela>/metadata --out .sparkforge-azure/facts.json
```

   Fatos esperados:
   - snapshots (id, timestamp, operação, summary)
   - número de manifests e data files por snapshot
   - spec de partição atual e histórico de evolução
   - propriedades de retenção (`history.expire.*`)
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain iceberg`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — snapshot citado existe no metadata.json mais recente; leitor externo e catálogo declarados no artefato.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Tabela é Delta com UniForm → `delta-lake` para o log Delta.
- Leitor externo não vê dados → comparar metadata pointer do catálogo antes de culpar o writer.
- Permissão de leitura → `unity-catalog`/`fabric-onelake`.
- Migração de catálogo AWS → `migration`.

## Não concluir sem evidência

- Não afirmar que expirar snapshots é seguro sem verificar leitores e time travel.
- Não tratar Glue ou Lake Formation como catálogo equivalente no Azure.
- Não afirmar consistência entre leitores sem evidência de metadata pointer.
- Não estimar ganho de compactação sem medição.

## Fronteiras

- Não trata Glue/Lake Formation como catálogo Azure.
- Não executa expire_snapshots/rewrite_data_files.
- Não cobre o log Delta (delta-lake).

## Handoff

- `delta-lake` — UniForm e log Delta.
- `unity-catalog` — catálogo e permissões no Databricks.
- `fabric-onelake` — tabelas Iceberg via OneLake.
- `migration` — migração de catálogo.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
