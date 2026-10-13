---
id: azure.adls.gen2
title: ADLS Gen2 - HNS, ABFSS, avaliação RBAC/ABAC/ACL, limites, rede e MI
domain: azure-adls
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.unity-catalog.troubleshooting-external-locations, azure.entra.managed-identity, azure.network.private-link-dns, governance.multi-layer-conflicts, azure.spark.performance-aqe-shuffle-skew]
---

# ADLS Gen2

## Básico

- ADLS Gen2 = conta de storage com **hierarchical namespace (HNS)**. Unity Catalog
  external locations exigem HNS.
- URI Spark: `abfss://<container>@<conta>.dfs.core.windows.net/<path>` (endpoint `dfs`).
- Configs `fs.azure.*` do driver ABFS: **não verificadas** nesta base — não sugerir
  chaves de config sem fonte.

## Ordem de avaliação de acesso (documentada)

1. Existe **role assignment** (RBAC) que cobre a ação?
   - Sim → há **condições ABAC**? Nenhuma → **concede**. Todas casam → **concede**.
     Alguma não casa → cai para ACL.
2. Sem role aplicável → avalia **ACL POSIX**.
3. ACL permite → concede; senão → **nega**.

Consequência: **ACL não restringe o que RBAC já concedeu.** Para restringir por pasta, não
dê role de dados em escopo amplo.

- **Shared Key** e SAS de conta/serviço **ignoram RBAC e ACL**. User delegation SAS pode
  ser checada contra ACL (parâmetro `suoid`).

## Roles de dados

| Role | Capacidade relevante |
|---|---|
| Storage Blob Data Owner | define owner, gerencia todas as ACLs |
| Storage Blob Data Contributor | leitura/escrita; ACL só em itens de que é owner |
| Storage Blob Data Reader | leitura |

Para UC: o MI do access connector precisa de **Storage Blob Data Contributor** (ou
Storage Blob Delegator + Contributor no container).

## ACL

- **Traverse**: `--X` em **todos** os diretórios pais; **listar**: `R-X` no diretório.
- Limite de **32 entradas** de ACL por arquivo/diretório (efetivamente 28 utilizáveis);
  ACL de acesso e default têm 32 cada.
- ACL default só afeta itens **criados depois** (não retroativa) — comportamento POSIX
  conhecido, não relido nesta verificação (UNVERIFIED).
- Recomendação: ACL para **grupos**, não usuários; manter membros de grupo < 200.
- Limite de **4000** role assignments por subscription.

## Layout e arquivos

- Tamanho alvo de arquivo: **256 MB – 100 GB**; operações cobradas em incrementos de 4 MB;
  arquivos pequenos aumentam overhead.
- Avro para write-heavy (ex.: Event Hubs Capture); Parquet/ORC para read-heavy.
- Se ACL varia por região/assunto, colocar a **data por último** no caminho.

## Rede

- Firewall da conta: VNets/IPs permitidos, **resource instances** (ex.: access connector
  Databricks) e exceção "Allow Azure trusted services".
- Private endpoints separados por subrecurso: `dfs` → `privatelink.dfs.core.windows.net`;
  `blob` → `privatelink.blob.core.windows.net`; `queue` → `privatelink.queue.core.windows.net`
  (file events usam fila).
- Diagnostic settings para storage/Event Hubs com VNet exigem "Allow trusted Microsoft
  services".

## Managed identity

- MI (system ou user-assigned) recebe role de dados; nenhum segredo trafega.
- Ver `azure.entra.managed-identity`.

## Fatos que o Forge extrai

- Role de dados em escopo de subscription/conta quando a intenção é por pasta.
- Uso de account key/SAS em código (bypass de RBAC/ACL).
- ACL próxima do limite de 32 entradas; ACL com usuários individuais.

## Fontes

- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings (retrieved: 2026-10-06)
