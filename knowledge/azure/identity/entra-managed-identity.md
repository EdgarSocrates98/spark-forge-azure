---
id: azure.entra.managed-identity
title: Entra ID - usuários, grupos, service principals, managed identities e RBAC
domain: azure-entra
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.keyvault.secrets-and-rbac, azure.adls.gen2, azure.unity-catalog.securable-model, governance.multi-layer-conflicts]
---

# Entra ID e managed identities

## Tipos de identidade

- **Humanas**: usuários (e grupos que os agregam).
- **Workload identities** (não humanas): **aplicações/service principals** e **managed
  identities**.
- Grupos são a unidade recomendada para RBAC e ACLs (ex.: ADLS recomenda ACL por grupo).

## Managed identity: system-assigned × user-assigned

| Propriedade | System-assigned | User-assigned |
|---|---|---|
| Criação | parte do recurso Azure | recurso Azure independente |
| Ciclo de vida | morre com o recurso | independente; apagar explicitamente |
| Compartilhamento | 1 recurso só | vários recursos |
| Uso típico | workload contido num recurso | vários recursos com mesma permissão; pré-autorização antes do deploy; recursos recriados com frequência |

- Ambos criam um **service principal especial** no Entra ID.
- Nome do SP system-assigned = nome do recurso.
- A Microsoft indica **user-assigned** como tipo recomendado para serviços Microsoft.
- Sem custo adicional; credenciais **não acessíveis** ao desenvolvedor.
- Tokens: SDK `Azure.Identity` (ou MSAL) obtém token Entra no ambiente, sem segredo.

## Workload identity federation

- Managed identity pode ser **Federated Identity Credential (FIC)** de uma app Entra:
  a workload troca o token da MI por token da app — recomendado quando uma app Entra é
  exigida, para ficar sem segredo. Limite de **20 FICs** por app nesse uso.

## RBAC Azure (control plane × data plane)

- Role assignment = principal + role definition + **escopo** (management group,
  subscription, resource group, recurso). Herda para escopos filhos.
- Control plane (gerir recurso) e data plane (ler dados) são **roles diferentes**: ex.
  `Key Vault Contributor` não lê segredos; `Contributor` em storage não lê blobs via
  Entra sem role de dados.
- ADLS: 4000 role assignments por subscription.
- Propagação de role assignment não é instantânea ("allow several minutes" na doc do Key
  Vault) — teste imediato pode falhar.

## OAuth / tokens nos serviços de dados

- Event Hubs Kafka: **OAUTHBEARER** com Entra ID + RBAC (alternativa a connection string).
- UC external locations: access connector com MI → storage credential.
- ADF/Synapse/Fabric: MI do factory/workspace em linked services/connections.

## Fatos que o Forge coleta

- Tipo de identidade usada por cada workload (MI system/user, SP com segredo, chave).
- Role assignments por escopo e se a role é de control plane ou data plane.
- Segredos de SP com expiração (quando visível) — risco operacional.

## O que NÃO afirmar

- Que um principal "tem acesso" só porque tem role de control plane (Owner/Contributor)
  no recurso.

## Não verificado

- Detalhes de grupos aninhados, PIM e Conditional Access (fora das páginas lidas).

## Fontes

- https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/event-hubs/azure-event-hubs-apache-kafka-overview (retrieved: 2026-10-06)
