---
id: governance.multi-layer-conflicts
title: Conflitos multicamada de governança - Entra, RBAC, ACL, UC, Purview, Fabric e rede
domain: governance
authority: internal
sources:
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.adls.gen2, azure.unity-catalog.securable-model, azure.unity-catalog.privileges-and-fgac, azure.unity-catalog.troubleshooting-external-locations, azure.entra.managed-identity, azure.network.private-link-dns, azure.purview.unified-catalog-and-lineage, azure.fabric.onelake-shortcuts]
---

# Conflitos multicamada de governança

## Por que existe

No Azure, "ter acesso" a um dado é a **conjunção** de camadas independentes. Cada uma tem
seu próprio modelo e pode negar sozinha. A síntese abaixo é **interna** (authority:
internal), derivada das fontes listadas.

| Camada | Pergunta | Quem decide |
|---|---|---|
| Entra ID | quem é o principal? token válido? | tenant |
| Azure RBAC (+ ABAC) | role de **dados** no escopo? | dono da subscription/recurso |
| ADLS ACL | POSIX permite (só quando RBAC não concedeu)? | dono do filesystem |
| Rede | o compute alcança o endpoint (firewall, PE, DNS)? | time de rede |
| Unity Catalog | grant UC + binding de workspace? | metastore/catalog admin |
| Fabric | papel de workspace/item + permissões OneLake/shortcut? | admin Fabric |
| Purview | **cataloga/classifica**; DLP/Information Protection | governança |

**Purview não concede acesso a tabelas UC**; Fabric tem governança nativa no OneLake
catalog; Purview adiciona DLP, Audit e Information Protection.

## Os 5 cenários canônicos

### 1. RBAC permite, ACL nega (ou o contrário)

- Fato documentado: com role de dados que concede (sem condição ABAC falhando), **a ACL
  não é avaliada** — ela não restringe. ACL só decide quando não há role aplicável.
- Sintoma típico: time configura ACL restritiva em pasta e "não funciona" porque o
  principal tem Storage Blob Data Reader na conta. O inverso: sem role, ACL sem `--X` em
  algum pai nega traverse.
- Evidência: role assignments no escopo + ACL de cada diretório do caminho.

### 2. Identidade válida, rede privada nega

- Token e permissões corretos, mas o storage tem acesso público desabilitado, o compute
  não está em VNet/resource instance permitida, ou o DNS resolve para IP público.
- Resolver o CNAME público não prova acesso; com acesso público desabilitado o serviço
  rejeita na borda.
- Evidência: networkRuleSet, PEs (Approved?), resolução DNS a partir do compute.

### 3. Permissão UC existe, storage credential falha

- `READ FILES` concedido na external location, mas o access connector (MI) não tem role
  no storage, está em outra região, ou não está em "Resource instances".
- Evidência: cadeia `azure.unity-catalog.troubleshooting-external-locations`.

### 4. Acesso ao workspace existe, catalog nega

- Usuário entra no workspace e tem grant, mas o catalog está **vinculado** a outros
  workspaces (binding sobrepõe grants), ou falta `USE CATALOG`/`USE SCHEMA`.
- Evidência: bindings do catalog; grants efetivos incluindo herança.

### 5. Acesso ao storage existe, external location nega

- Principal tem role no ADLS (lê via SAS/abfss direto em dedicated compute), mas via UC
  recebe negação: falta `READ FILES`, `WRITE FILES` sem `READ FILES`
  (`PERMISSION_DENIED`), ou location `ISOLATED` sem o workspace.
- Em standard compute, DBUtils só lê cloud storage **via external location**.

## Cenários Fabric relacionados

- Shortcut interno: identidade do **chamador** precisa de permissão no alvo; exceção
  Direct Lake over SQL / T-SQL delegated mode usa o **dono do item**.
- Shortcut externo: autorização pela **cloud connection** (bind exige permissão nela).

## Saída do diagnóstico (contrato)

- Uma linha por camada: `ok | fail | unresolved`, com evidência.
- `unresolved` é explícito: camada sem dado coletado **não** é "ok".
- Conflito declarado quando duas camadas dão vereditos opostos com evidência.

## Fontes

- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric (retrieved: 2026-10-06)
