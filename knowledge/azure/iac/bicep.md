---
id: azure.iac.bicep
title: Bicep para infraestrutura de dados no Azure
domain: azure-bicep
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview
    retrieved: 2026-10-06
  - url: https://github.com/Azure/bicep/releases
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {bicep: ["0.48.1"]}
status: VERIFIED
preview: false
related: [azure.iac.terraform-azurerm, azure.observability.monitor-log-analytics, azure.adls.gen2]
---

# Bicep

## O que é

- DSL declarativa para recursos Azure; o Bicep CLI **transpila para ARM JSON** no deploy.
  Tudo que vale em ARM template (tipos, API versions, propriedades) vale em Bicep.
- Suporta imediatamente **todas** as API versions, preview e GA, de cada resource provider.
- **Sem state file**: o Azure guarda o estado; deploy é idempotente.
- **what-if** mostra o que será criado/alterado/apagado antes do deploy.
- Módulos para reuso; dependências inferidas por nome simbólico (sem `dependsOn` manual na
  maioria dos casos).
- Gratuito e open source; versão mais recente verificada **v0.48.1** (2026-10-05);
  features específicas dessa versão: UNVERIFIED.
- Features **experimentais** do Bicep não têm suporte da Microsoft.

## Exemplo — diagnostic setting (da doc de Azure Monitor)

```bicep
param scope string
param workspaceId string
param settingName string

resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: settingName
  scope: scope
  properties: {
    workspaceId: workspaceId
    logs: [ { category: null, categoryGroup: 'audit', enabled: true } ]
  }
}
```

Note a API version `-preview`: o Forge marca recursos com API preview como PREVIEW no
inventário, sem tratá-los como erro.

## Bicep × Terraform (para o Forge)

| Critério | Bicep | Terraform |
|---|---|---|
| Estado | no Azure | state file (remoto recomendado) |
| Preview APIs | imediato | via `azapi` |
| Databricks UC (grants, locations) | não cobre o plano de dados Databricks | provider `databricks` |
| Preview de mudança | what-if | plan |

Combinação comum: Bicep/Terraform azurerm para recursos Azure + provider `databricks`
para objetos UC.

## Review determinístico de Bicep

- `@secure()` em parâmetros de segredo; ausência = achado.
- API versions antigas/preview fixadas; recursos de storage sem `isHnsEnabled` quando a
  intenção é UC/ADLS (propriedade não relida — UNVERIFIED).
- Nunca executar deploy; what-if só com autorização.

## Não verificado

- Recursos específicos da v0.48.1; nomes de propriedades ARM de storage/Databricks citados
  como exemplo de review.

## Fontes

- https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview (retrieved: 2026-10-06)
- https://github.com/Azure/bicep/releases (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings (retrieved: 2026-10-06)
