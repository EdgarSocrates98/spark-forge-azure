---
name: azure-terraform
description: 'Use para Terraform com providers azurerm, azapi e databricks: revisão de PR de infraestrutura
  de dados, plan JSON, módulos de workspace Databricks, storage, private endpoints, role assignments,
  UC via provider databricks. Sintomas: ''esse plan destrói algo?'', segredo em tfvars, RBAC amplo em
  código, drift. Lê HCL e plan; nunca executa apply.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - terraform
  - azurerm
  - tfplan
  - terraform plan
  - databricks provider
  - hcl
  - tfvars
  scope:
  - Terraform
  - azurerm
  - azapi
  - databricks provider
  - plan JSON
  - módulos
  does:
  - extrai recursos, atributos e dependências do HCL
  - classifica ações do plan JSON (create/update/replace/destroy)
  - liga recursos IaC a findings de governança e rede
  does_not:
  - não executa plan/apply nem acessa state remoto
  - não cobre Bicep/ARM (azure-bicep)
  - não decide desenho de rede sozinho (azure-networking)
  knowledge_refs:
  - knowledge/azure/iac/
  tool_refs:
  - sparkforge-azure analyze terraform
  - sparkforge-azure graph impact
  - sfa_analyze
  - sfa_graph_impact
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-terraform/evals/evals.yaml
  source_authority:
  - hashicorp_official
  - microsoft_official
  - databricks_official
---

# Terraform para Azure Data

IaC é intenção declarada. O plan JSON é a melhor evidência do que mudaria; o HCL sozinho não prova estado.

## Quando usar

- `terraform`
- `azurerm`
- `tfplan`
- `terraform plan`
- `databricks provider`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — arquivos `.tf`, `terraform show -json` do plan gerado pelo usuário, módulos referenciados, `.tfvars` (sem valores sensíveis). Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze terraform --path infra/ --out .sparkforge-azure/facts.json
sparkforge-azure graph impact --node tf:azurerm_storage_account.<name>
```

   Fatos esperados:
   - recursos por tipo e endereço
   - ações do plan: replace/destroy em recursos com dados
   - role assignments e escopos declarados
   - segredos literais em HCL/tfvars (só o caminho)
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-terraform`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — ação citada vem do plan JSON; sem plan, falar de "HCL declara", nunca de "vai acontecer".
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Replace em storage account/workspace → finding de risco de dados.
- Role assignment amplo → `security-reviewer`/`azure-entra`.
- Private endpoint/DNS no HCL → `azure-networking`.
- Recurso UC no provider databricks → `unity-catalog`.

## Não concluir sem evidência

- Nunca executar apply nem sugerir `-auto-approve`.
- Não afirmar que o plan "não destrói nada" sem plan JSON.
- Não afirmar ausência de drift sem state/plan atual.
- Não imprimir valores de variáveis sensíveis.

## Fronteiras

- Não executa plan/apply nem acessa state remoto.
- Não cobre Bicep/ARM (azure-bicep).
- Não decide desenho de rede sozinho (azure-networking).

## Handoff

- `security-reviewer` — RBAC amplo, segredo, exposição pública.
- `azure-networking` — rede declarada.
- `unity-catalog` — recursos UC no provider databricks.
- `azure-bicep` — parte da infra está em Bicep.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
