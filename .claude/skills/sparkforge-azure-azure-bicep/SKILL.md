---
name: sparkforge-azure-azure-bicep
description: 'Use para Bicep e templates ARM de plataformas de dados: workspace Databricks, storage, Key
  Vault, private endpoints, ADF, Event Hubs, role assignments. Sintomas: revisão de PR Bicep, resultado
  de what-if, parâmetro com segredo, módulo sem dependência explícita, ''esse deployment recria o workspace?''.
  Lê .bicep/.bicepparam e what-if exportado; nunca faz deploy.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - bicep
  - arm template
  - what-if
  - bicepparam
  - deployment azure
  scope:
  - Bicep
  - ARM templates
  - what-if
  - módulos Bicep
  - parâmetros
  does:
  - extrai recursos, API versions e dependências
  - classifica mudanças do what-if exportado
  - detecta segredo em parâmetro sem `@secure()`
  does_not:
  - não executa deployment nem what-if
  - não cobre Terraform (azure-terraform)
  - não decide desenho de identidade (azure-entra)
  knowledge_refs:
  - knowledge/azure/iac/
  tool_refs:
  - sparkforge-azure graph build
  - sparkforge-azure graph impact
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  planned_tool_refs:
  - sparkforge-azure analyze bicep
  eval_refs:
  - skills/azure-bicep/evals/evals.yaml
  source_authority:
  - microsoft_official
---
<!-- GENERATED from skills/azure-bicep/SKILL.md; do not edit -->
# Bicep / ARM

IaC nativo do Azure. O what-if exportado é a evidência de mudança; o template sozinho só declara intenção.

## Quando usar

- `bicep`
- `arm template`
- `what-if`
- `bicepparam`
- `deployment azure`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — arquivos `.bicep`, `.bicepparam`, ARM JSON compilado, resultado de `what-if` exportado pelo usuário. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure graph build --root infra/
sparkforge-azure graph impact --graph .sparkforge-azure/graph/graph.json --changed infra/main.bicep
# Sem extrator de template ainda (planned_tool_refs): fatos de módulos/recursos
# entram em .sparkforge-azure/facts.json montados a mão a partir dos .bicep.
```

   Fatos esperados:
   - recursos, API versions e escopo de deployment
   - mudanças do what-if (Create, Modify, Delete, Deploy)
   - parâmetros sensíveis sem `@secure()`
   - role assignments e escopos
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-bicep`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — mudança citada vem do what-if; sem what-if, falar de "template declara".
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Delete/recreate em recurso com dados → finding de risco.
- API version antiga → comparar com knowledge datado antes de afirmar.
- RBAC amplo → `security-reviewer`.
- Rede/PE → `azure-networking`.

## Não concluir sem evidência

- Nunca executar deployment.
- Não afirmar que o deployment é idempotente sem what-if.
- Não imprimir valores de parâmetros seguros.
- Não afirmar API version "mais recente" sem data do knowledge.

## Fronteiras

- Não executa deployment nem what-if.
- Não cobre Terraform (azure-terraform).
- Não decide desenho de identidade (azure-entra).

## Handoff

- `security-reviewer` — segredo, RBAC amplo, exposição.
- `azure-networking` — rede declarada.
- `azure-terraform` — parte da infra em Terraform.
- `azure-entra` — identidades declaradas.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
