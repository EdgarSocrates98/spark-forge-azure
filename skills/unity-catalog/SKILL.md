---
name: unity-catalog
description: 'Use quando houver acesso negado, PERMISSION_DENIED, grant faltando, external location ou
  storage credential mal configurada, workspace binding, ownership de catálogo/schema/tabela/volume no
  Unity Catalog. Também para ''por que o usuário vê a tabela mas não lê os arquivos'' e diagnóstico multicamada
  UC + ADLS + Entra + rede. Evidência: grants JSON, external locations, credentials, bindings. Conceitos
  de Lake Formation não são aliases de UC.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - unity catalog
  - permission_denied
  - grant
  - external location
  - storage credential
  - workspace binding
  - acesso negado
  - metastore
  scope:
  - Unity Catalog
  - catalog
  - schema
  - table
  - volume
  - external location
  - storage credential
  - workspace binding
  does:
  - diagnostica cadeia de privilégios UC (USE CATALOG → USE SCHEMA → SELECT)
  - liga external location → storage credential → managed identity
  - separa camada UC de camadas ADLS/Entra/rede com evidência
  does_not:
  - não trata Lake Formation/Glue como sinônimo de UC
  - não altera grants (somente leitura)
  - não diagnostica ACL POSIX de ADLS sozinho (azure-adls)
  knowledge_refs:
  - knowledge/azure/unity-catalog/
  - knowledge/governance/
  tool_refs:
  - sparkforge-azure governance diagnose
  - sparkforge-azure analyze uc-grants
  - sparkforge-azure graph query
  - sfa_governance_diagnose
  - sfa_graph_query
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/unity-catalog/evals/evals.yaml
  source_authority:
  - databricks_official
  - microsoft_official
---

# Unity Catalog

Governança do Databricks. Acesso só é explicado quando cada camada da cadeia tem evidência própria.

## Quando usar

- `unity catalog`
- `permission_denied`
- `grant`
- `external location`
- `storage credential`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — export de grants (`SHOW GRANTS`/API), external locations, storage credentials, workspace bindings, owner de cada securable. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze uc-grants --path exports/uc/ --out .sparkforge-azure/facts.json
sparkforge-azure governance diagnose --scenario uc-read-denied --facts .sparkforge-azure/facts.json
sparkforge-azure graph query --from principal:<id> --to table:<catalog.schema.table>
```

   Fatos esperados:
   - privilégios efetivos por principal e securable (USE CATALOG → USE SCHEMA → SELECT, incluindo herança por grupo)
   - owner de catálogo/schema/tabela
   - external location → URL abfss → storage credential → access connector/MI
   - bindings catálogo ↔ workspace
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain unity-catalog`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — refazer a cadeia com `graph query`; cada elo sem evidência vira `unresolved`, nunca "provavelmente ok".
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Grant UC presente e erro persiste ao ler arquivos → `azure-adls` (RBAC/ACL do access connector).
- Erro só a partir de certo workspace → checar binding antes de grants.
- Principal é grupo do Entra não sincronizado → `azure-entra`.
- Storage com firewall/private endpoint → `azure-networking`.

## Não concluir sem evidência

- Não afirmar que o principal "tem acesso" sem privilégio efetivo em todos os níveis.
- Não mapear Lake Formation permission ou Glue database para UC como equivalente.
- Não dizer "seguro"; dizer "casos de ameaça declarados passaram".
- Não supor herança de grupo sem membership exportado.

## Fronteiras

- Não trata Lake Formation/Glue como sinônimo de UC.
- Não altera grants (somente leitura).
- Não diagnostica ACL POSIX de ADLS sozinho (azure-adls).

## Handoff

- `azure-adls` — UC autoriza mas leitura de arquivo falha.
- `azure-entra` — identidade, grupo ou managed identity em dúvida.
- `azure-networking` — storage atrás de private endpoint/firewall.
- `azure-purview` — pergunta de lineage ou classificação.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
