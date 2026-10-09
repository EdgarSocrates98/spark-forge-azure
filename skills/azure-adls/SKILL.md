---
name: azure-adls
description: 'Use para ADLS Gen2 e storage accounts: ACL POSIX, RBAC de dados (Storage Blob Data Reader/Contributor),
  hierarchical namespace, firewall de storage, abfss. Sintomas: 403 AuthorizationPermissionMismatch, ''RBAC
  deu acesso mas a ACL nega'', access connector do Databricks sem permissão, shortcut OneLake falhando
  na origem. Faz parte do diagnóstico multicamada de governança.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - adls
  - abfss
  - acl
  - authorizationpermissionmismatch
  - storage blob data
  - hierarchical namespace
  - 403 storage
  scope:
  - ADLS Gen2
  - storage account
  - ACL POSIX
  - RBAC de dados
  - containers
  - firewall de storage
  does:
  - avalia RBAC de dados + ACL (acesso e default) por caminho
  - identifica execute faltando em diretórios pais
  - liga principal (MI/SP/usuário) à permissão efetiva
  does_not:
  - não decide grants de Unity Catalog (unity-catalog)
  - não diagnostica DNS/private endpoint sozinho (azure-networking)
  - não altera ACL/RBAC
  knowledge_refs:
  - knowledge/azure/storage/
  - knowledge/azure/identity/
  - knowledge/governance/
  tool_refs:
  - sparkforge-azure collect adls-meta
  - sparkforge-azure collect azure-rbac
  - sparkforge-azure governance diagnose
  - sfa_governance_diagnose
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze adls-acl
  eval_refs:
  - skills/azure-adls/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# ADLS Gen2

Camada de armazenamento. Permissão efetiva = RBAC de dados OU ACL avaliada caminho a caminho; nenhuma é presumida.

## Quando usar

- `adls`
- `abfss`
- `acl`
- `authorizationpermissionmismatch`
- `storage blob data`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — dump de ACL por caminho (inclusive diretórios pais), role assignments no escopo account/container, storage account JSON (HNS, firewall, shared key). Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure collect adls-meta --export exports/adls.json --facts
sparkforge-azure collect azure-rbac --export exports/rbac.json --facts
sparkforge-azure governance diagnose --scenario .sparkforge-azure/cenario.yaml
```

   Salve a saída dos collectors em `.sparkforge-azure/facts.json` — `judge` aceita o
   envelope `fact_list`. O cenário de governance é um YAML composto dos artefatos;
   formato em `examples/governance/uc_external_location_denied.yaml`.

   Fatos esperados:
   - role assignments de dados por principal e escopo
   - ACL de acesso e default em cada segmento do caminho
   - execute (x) em todos os diretórios pais
   - HNS habilitado, firewall, acesso público, shared key
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-adls`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — avaliar a cadeia completa raiz → arquivo; segmento sem ACL exportada vira `unresolved`.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Principal é access connector do Databricks → confirmar MI e voltar para `unity-catalog` com o resultado.
- Firewall/private endpoint presente → `azure-networking`.
- Principal é grupo → membership do `azure-entra`.
- Origem de shortcut OneLake → devolver ao `fabric-onelake`.

## Não concluir sem evidência

- Não afirmar acesso só porque há RBAC de leitura em outro escopo.
- Não ignorar execute nos diretórios pais.
- Não dizer "seguro"; dizer "casos de ameaça declarados passaram".
- Não supor ACL default aplicada a arquivos já existentes.

## Fronteiras

- Não decide grants de Unity Catalog (unity-catalog).
- Não diagnostica DNS/private endpoint sozinho (azure-networking).
- Não altera ACL/RBAC.

## Handoff

- `azure-entra` — identidade, grupo, managed identity.
- `azure-networking` — firewall, private endpoint, DNS.
- `unity-catalog` — camada UC acima do storage.
- `fabric-onelake` — origem de shortcut.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
