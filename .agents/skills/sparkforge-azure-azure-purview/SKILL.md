---
name: sparkforge-azure-azure-purview
description: 'Use para Microsoft Purview: data map, scans, classificações, sensitivity labels, glossário
  e lineage exportados. Sintomas: lineage faltando entre ADF e Databricks, scan falhando por credencial,
  ativo sem classificação, ''quais tabelas têm PII?''. Purview cataloga e informa; não é a camada que
  aplica acesso do Unity Catalog.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - purview
  - lineage
  - data map
  - scan purview
  - classification
  - sensitivity label
  - glossário
  scope:
  - Microsoft Purview
  - data map
  - scans
  - classificações
  - lineage
  - glossário
  does:
  - lê exports de lineage/scan/classificação
  - aponta lacunas de lineage entre sistemas
  - liga ativos Purview a recursos por ID qualificado
  does_not:
  - não aplica nem decide acesso do Unity Catalog (unity-catalog)
  - não classifica dados por amostragem própria
  - não afirma completude de lineage
  knowledge_refs:
  - knowledge/azure/purview/
  - knowledge/governance/
  tool_refs:
  - sparkforge-azure analyze purview-lineage
  - sparkforge-azure graph query
  - sfa_analyze
  - sfa_graph_query
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-purview/evals/evals.yaml
  source_authority:
  - microsoft_official
---
<!-- GENERATED from skills/azure-purview/SKILL.md; do not edit -->
# Microsoft Purview

Catálogo e lineage corporativo. Lineage exportado é evidência do que foi capturado, não do que existe.

## Quando usar

- `purview`
- `lineage`
- `data map`
- `scan purview`
- `classification`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — export de lineage (processos, entradas, saídas), resultados de scan, classificações e labels por ativo, glossário. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze purview-lineage --path exports/purview/ --out .sparkforge-azure/facts.json
sparkforge-azure graph query --from purview:<qualifiedName> --direction downstream
```

   Fatos esperados:
   - ativos com qualifiedName e tipo
   - arestas de lineage e o processo que as produziu
   - classificações/labels por ativo
   - scans com status e credencial referenciada
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-purview`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — ativo citado tem qualifiedName no export; aresta citada tem processo de origem.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Pergunta de acesso efetivo → `unity-catalog`/`azure-adls`.
- Scan falhando por credencial → `azure-entra`.
- Lineage ausente de job Databricks → verificar se a origem emite lineage antes de concluir lacuna.
- Pergunta de PII sem classificação exportada → `unresolved`.

## Não concluir sem evidência

- Não afirmar lineage "completo".
- Não afirmar que um ativo não tem PII por falta de classificação.
- Não tratar label do Purview como controle de acesso aplicado no UC.
- Não inventar qualifiedName.

## Fronteiras

- Não aplica nem decide acesso do Unity Catalog (unity-catalog).
- Não classifica dados por amostragem própria.
- Não afirma completude de lineage.

## Handoff

- `unity-catalog` — acesso efetivo e grants.
- `azure-entra` — credenciais de scan.
- `azure-data-factory` — lineage de pipelines ADF.
- `azure-databricks` — emissão de lineage do Databricks.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
