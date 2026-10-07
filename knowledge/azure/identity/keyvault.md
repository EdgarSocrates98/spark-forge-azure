---
id: azure.keyvault.secrets-and-rbac
title: Azure Key Vault - RBAC vs access policies, roles e integração com Databricks/ADF
domain: azure-keyvault
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/security/secrets/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {keyvault_api: ["2026-02-01"]}
status: VERIFIED
preview: false
related: [azure.entra.managed-identity, azure.databricks.runtime-and-compute, azure.adf.pipelines-ir-managed-vnet, azure.network.private-link-dns]
---

# Azure Key Vault

## Planos de acesso

| Plano | Endpoint | Autorização |
|---|---|---|
| Control plane | `management.azure.com` | Azure RBAC |
| Data plane | `<vault>.vault.azure.net` | **Azure RBAC** ou access policy (legado) |

- A partir da **API 2026-02-01**, **Azure RBAC é o modelo default** para vaults novos.
- Trocar para RBAC **invalida todas as access policies** — pode causar indisponibilidade
  se roles equivalentes não forem atribuídas antes.
- Mudar o modelo exige `Microsoft.Authorization/roleAssignments/write` irrestrito (Owner ou
  User Access Administrator + `Microsoft.KeyVault/vaults/write`).
- Quem tem `Contributor` no control plane com modelo access policy pode **se dar** acesso
  ao data plane: controlar `Contributor`.

## Roles de data plane

| Role | Capacidade |
|---|---|
| Key Vault Administrator | tudo no data plane (não gerencia role assignments) |
| Key Vault Secrets Officer | qualquer ação em segredos, exceto permissões |
| **Key Vault Secrets User** | ler conteúdo de segredos (mínimo para workloads) |
| Key Vault Reader | metadados, **sem** valores |
| Key Vault Crypto Officer / Crypto User / Crypto Service Encryption User | chaves |
| Key Vault Certificates Officer / Certificate User | certificados |
| Key Vault Data Access Administrator | gerencia atribuições das roles acima (com condição ABAC) |

- `Key Vault Contributor` é **só control plane**: não lê segredos.
- ABAC para Key Vault (condições) está em **preview** e só para ações de segredo.
- Recomendação: um vault por aplicação por ambiente; roles no escopo do vault; evitar
  roles por segredo (exceto casos citados).
- Propagação de role assignment: "vários minutos".

## Integração Databricks — conflito conhecido

- Secret scope **Azure Key Vault-backed** suporta **apenas Vault access policy**, não
  Azure RBAC. Com vault em RBAC (default novo), o scope AKV-backed exige trocar o modelo
  do vault para access policy — decisão de segurança a registrar, não a "consertar" em
  silêncio.
- Criar o scope exige Contributor/Owner/Key Vault Contributor no vault; concede Get/List
  ao app do Databricks via access policy.
- Firewall do vault: "Allow trusted Microsoft services" ou acesso público por VNets/IPs.
- ACL do scope dá acesso a **todos** os segredos do vault: separar vaults para isolar.

## Integração ADF / Fabric

- ADF: linked service de Key Vault não referencia IR; PE do Key Vault na managed VNet é
  criado via linked service de data store; "test connection" só valida URL.
- SHIR suporta Key Vault; **OPDG do Fabric não** (credenciais no gateway).

## Rede

- Private DNS zone: `privatelink.vaultcore.azure.net` (vault);
  `privatelink.managedhsm.azure.net` (Managed HSM).

## Fatos que o Forge coleta

- Modelo de permissão do vault (RBAC × access policy) × uso de scope AKV-backed.
- Atribuições amplas (Administrator/Secrets Officer) para workloads que só leem.

## Fontes

- https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/security/secrets/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/data-factory/managed-virtual-network-private-endpoint (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory (retrieved: 2026-10-06)
