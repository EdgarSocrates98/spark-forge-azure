---
id: azure.unity-catalog.troubleshooting-external-locations
title: Troubleshooting de external locations UC no ADLS - cadeia de falhas
domain: unity-catalog
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-adls
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.unity-catalog.securable-model, azure.unity-catalog.privileges-and-fgac, azure.adls.gen2, azure.entra.managed-identity, azure.network.private-link-dns, governance.multi-layer-conflicts]
---

# Troubleshooting de external locations (UC → ADLS Gen2)

## Princípio

Uma leitura/escrita por external location atravessa **seis camadas**. Cada uma pode negar
sozinha. O Forge percorre a cadeia **na ordem** e para no primeiro elo sem evidência,
marcando os elos seguintes como `unresolved` — nunca como "ok".

```
principal --(grant UC)--> external location --(binding)--> workspace
external location --> storage credential --> access connector (MI)
MI --(RBAC/ABAC)--> conta ADLS --(ACL POSIX)--> path
rede: compute --(firewall / private endpoint / DNS)--> conta ADLS
```

## Cadeia de falhas (ordem de verificação)

| # | Camada | Pergunta | Evidência a coletar |
|---|---|---|---|
| 1 | Storage credential | aponta para o access connector certo? | `DESCRIBE STORAGE CREDENTIAL`, resource id do connector |
| 2 | Access connector MI | MI habilitada (system/user-assigned), mesma região do storage? | ARM do `Microsoft.Databricks/accessConnectors` |
| 3 | ADLS RBAC | MI tem Storage Blob Data Contributor (ou Delegator + container Contributor)? | role assignments no escopo conta/container |
| 4 | ADLS ACL | se não há role, ACL concede? `--X` em todos os pais, `R-X` para listar | ACL de cada diretório do caminho |
| 5 | Firewall / Private Endpoint | conta com acesso público desabilitado? connector em "Resource instances"? "Allow Azure trusted services"? DNS privado resolve? | networkRuleSet, PEs, zona `privatelink.dfs.core.windows.net` |
| 6 | Workspace binding | location em `ISOLATED` sem o workspace atual? | bindings da location/credential |

Mais o lado UC: `READ FILES`/`WRITE FILES` na location (e `CREATE EXTERNAL LOCATION` no
metastore **e** no credential para criar).

## Fatos documentados que explicam falhas

- **RBAC vence ACL quando concede**: se há role que concede (sem condição ABAC que
  falhe), a ACL não restringe. ACL só decide quando não há role aplicável.
- `WRITE FILES` sem `READ FILES` → `PERMISSION_DENIED` (erro citado na doc).
- VNet injection + firewall: adicionar o access connector em **Networking → Resource
  instances**; com acesso público desabilitado, habilitar **"Allow Azure trusted services"**
  (`--bypass AzureServices`).
- File events: se o credential não tem as roles extras, a criação emite **aviso de
  validação**; opções: "Force create" ou `enable_file_events=false`.
- Flag read-only pode levar até 60 min para propagar — teste logo após mudar pode enganar.
- Caminho com caracteres não ASCII, conta sem HNS, container com WORM/immutability:
  não suportados.
- DNS de private endpoint: zona `privatelink.dfs.core.windows.net` (dfs) e
  `privatelink.blob.core.windows.net` (blob). Não misturar serviços na mesma zona.

## Strings de erro

Somente strings encontradas em doc oficial são citadas: `PERMISSION_DENIED` (WRITE FILES
sem READ FILES). Strings como `AuthorizationPermissionMismatch` ou HTTP 403 de firewall
**não** foram encontradas nas páginas lidas — não citar como evidência; registrar a
mensagem observada no log do cliente como fato bruto.

## Saída esperada do diagnóstico

```yaml
chain:                      # status: ok | fail | unresolved
  - {layer: storage_credential, status: ok, evidence: [describe_credential]}
  - {layer: access_connector_mi, status: ok, evidence: [arm_access_connector]}
  - {layer: adls_rbac, status: fail, evidence: [role_assignments]}
  - {layer: adls_acl, status: unresolved, evidence: []}
  - {layer: network, status: unresolved, evidence: []}
  - {layer: workspace_binding, status: ok, evidence: [bindings]}
first_failure: adls_rbac
unresolved: [adls_acl, network]
```

## Não verificado

- Mensagens de erro exatas de RBAC/firewall vindas do ABFS driver.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-adls (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
