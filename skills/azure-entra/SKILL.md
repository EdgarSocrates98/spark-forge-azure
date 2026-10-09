---
name: azure-entra
description: 'Use para identidade em Azure data: Entra ID, managed identity (system/user), service principal,
  workload identity, role assignments (RBAC de controle e de dados), grupos e Key Vault/secret scopes.
  Sintomas: ''qual identidade o job usa?'', SP com Owner na subscription, segredo expirado, access connector
  sem role, grupo não sincronizado com o Databricks.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - entra
  - managed identity
  - service principal
  - role assignment
  - rbac
  - key vault
  - workload identity
  - secret scope
  scope:
  - Entra ID
  - managed identity
  - service principal
  - RBAC
  - Key Vault
  - secret scopes
  does:
  - resolve qual identidade cada recurso usa
  - avalia role assignments por escopo e privilégio excessivo
  - verifica referência a segredo (Key Vault/secret scope) sem ler valores
  does_not:
  - não lê nem imprime segredos
  - não decide grants UC (unity-catalog) nem ACL ADLS (azure-adls)
  - não cria nem altera assignments
  knowledge_refs:
  - knowledge/azure/identity/
  - knowledge/governance/
  tool_refs:
  - sparkforge-azure collect azure-rbac
  - sparkforge-azure governance diagnose
  - sparkforge-azure collect workspace-graph
  - sfa_governance_diagnose
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze role-assignments
  eval_refs:
  - skills/azure-entra/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# Microsoft Entra ID e identidades

Identidade é o elo comum entre UC, ADLS, ADF e rede. Toda conclusão nomeia o principal por object ID.

## Quando usar

- `entra`
- `managed identity`
- `service principal`
- `role assignment`
- `rbac`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — role assignments (ARG/export), descritores de MI/SP (object ID, app ID), membership de grupos, Key Vault JSON (RBAC vs access policy), secret scopes. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure collect azure-rbac --export exports/rbac.json --facts
sparkforge-azure governance diagnose --scenario .sparkforge-azure/cenario.yaml
sparkforge-azure collect workspace-graph --manifest sparkforge-azure.workspace.yaml --export exports/resource-graph.json   # opt-in, read-only
```

   Fatos esperados:
   - principal (object ID) por recurso consumidor
   - assignments por escopo (management group → subscription → RG → recurso)
   - roles privilegiadas (Owner, User Access Administrator, Contributor) em escopo amplo
   - modelo de autorização do Key Vault e referências de segredo
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-entra`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — principal citado por object ID existe no export; escopo herdado mostrado com o caminho completo.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Permissão de dados em storage → `azure-adls` com o principal resolvido.
- Key Vault atrás de private endpoint → `azure-networking`.
- Grupo usado no UC → `unity-catalog` com membership.
- Privilégio amplo encontrado → `security-reviewer`.

## Não concluir sem evidência

- Nunca imprimir valor de segredo, token ou connection string.
- Não afirmar least privilege sem inventário completo de assignments.
- Não identificar principal por display name sozinho.
- Não dizer "seguro"; dizer "casos de ameaça declarados passaram".

## Fronteiras

- Não lê nem imprime segredos.
- Não decide grants UC (unity-catalog) nem ACL ADLS (azure-adls).
- Não cria nem altera assignments.

## Handoff

- `azure-adls` — permissão de dados no storage.
- `unity-catalog` — grants para grupos/principals.
- `azure-networking` — Key Vault/recursos com private endpoint.
- `security-reviewer` — privilégio excessivo ou segredo exposto.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
