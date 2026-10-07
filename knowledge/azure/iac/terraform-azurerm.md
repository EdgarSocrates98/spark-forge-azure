---
id: azure.iac.terraform-azurerm
title: Terraform no Azure de dados - azurerm, azapi e databricks providers
domain: azure-terraform
authority: terraform_official
sources:
  - url: https://registry.terraform.io/v1/providers/hashicorp/azurerm
    retrieved: 2026-10-06
  - url: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/databricks_access_connector
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {azurerm: ["5.8.0"], databricks_provider: ["1.136.0"], azapi: ["2.13.0"], terraform: ["1.16.5"]}
status: VERIFIED
preview: false
related: [azure.iac.bicep, azure.unity-catalog.securable-model, azure.adls.gen2, azure.network.private-link-dns]
---

# Terraform para Azure Data

## Versões verificadas (registry/GitHub, 2026-10-06)

| Componente | Versão |
|---|---|
| `hashicorp/azurerm` | **5.8.0** (2026-10-01) — major 5 |
| `databricks/databricks` | 1.136.0 (2026-10-05) |
| `azure/azapi` | 2.13.0 (2026-09-28) |
| Terraform CLI | 1.16.5 (2026-10-02) |

- Guia de upgrade azurerm 4 → 5: **não lido** — não afirmar breaking changes específicos.

## Recursos relevantes

| Camada | Recurso | Status |
|---|---|---|
| Azure | `azurerm_databricks_access_connector` (name, resource_group_name, location, bloco identity) | existência VERIFIED; enum de `identity.type` UNVERIFIED |
| Azure | `azurerm_role_assignment` (MI → Storage Blob Data Contributor) | conceito; schema não relido |
| UC | `databricks_storage_credential`, `databricks_external_location` | existência VERIFIED (links da doc UC) |
| UC | grants e bindings (`databricks_grants`, workspace bindings) | não relidos |

## Padrão UC + ADLS (ordem de dependência)

1. Storage account HNS + container.
2. Access connector com MI (mesma região do storage).
3. Role assignment do MI no storage (Storage Blob Data Contributor; + roles de file events
   se usadas).
4. Regras de rede do storage: resource instance do connector / trusted services.
5. `databricks_storage_credential` → `databricks_external_location` → grants
   (`READ FILES` + `WRITE FILES` juntos) → bindings se `ISOLATED`.

Role assignment tem atraso de propagação: criar a external location imediatamente após o
role pode falhar a validação — modelar dependência e/ou retry.

## Princípios para o Forge (review de IaC)

- Fatos de HCL: versão de provider fixada? (`required_providers` com constraint); state
  remoto; recursos com segredo em plain text (`*_key`, connection strings).
- Nunca rodar `apply`: o Forge lê plano/HCL; `plan` só com autorização explícita.
- `azapi` cobre APIs ainda não expostas no azurerm (preview de serviço): marcar recurso
  como PREVIEW quando a API version é `-preview`.

## Não verificado

- Breaking changes do azurerm 5.0; enum de identity do access connector; schemas de
  `databricks_grants`/bindings.

## Fontes

- https://registry.terraform.io/v1/providers/hashicorp/azurerm (retrieved: 2026-10-06)
- https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/databricks_access_connector (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations (retrieved: 2026-10-06)
