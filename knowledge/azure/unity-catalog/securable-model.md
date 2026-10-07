---
id: azure.unity-catalog.securable-model
title: Unity Catalog - modelo de securables, external locations, credentials e bindings
domain: unity-catalog
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-adls
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.unity-catalog.privileges-and-fgac, azure.unity-catalog.troubleshooting-external-locations, azure.adls.gen2, azure.entra.managed-identity, governance.multi-layer-conflicts]
---

# Unity Catalog — modelo de securables

## Hierarquia

```
metastore (1 por região, N workspaces)
├── catalog
│   └── schema
│       ├── table (managed | external | foreign)
│       ├── view (+ materialized view, metric view)
│       ├── volume (managed | external)
│       ├── function (UDF, stored procedure, registered model)
│       ├── model
│       ├── service (Beta)   ├── secret   └── feature (Public Preview)
├── storage credential      ├── external location
├── service credential      ├── connection (Lakehouse Federation)
├── external metadata       ├── share / provider / recipient
└── clean room
```

- UC é habilitado automaticamente para workspaces criados após **2023-11-09**.
- Registered models são implementados como funções; privilégios de modelo: `CREATE MODEL`,
  `CREATE MODEL VERSION`, `APPLY TAG`, `EXECUTE`.

## Herança e caminho de acesso

- Ler uma tabela exige **`USE CATALOG`** + **`USE SCHEMA`** + privilégio no objeto
  (ex.: `SELECT`).
- Grants em catalog/schema **herdam** para os filhos; grants no **metastore não herdam**.
- `BROWSE` só em nível de catalog.

## Storage credential, access connector e external location

- **Access connector for Azure Databricks** (`Microsoft.Databricks/accessConnectors`):
  recurso Azure com managed identity system-assigned e/ou user-assigned, **mesma região**
  do storage.
- **Storage credential** referencia o access connector (MI); **external location** =
  storage credential + caminho `abfss://container@conta.dfs.core.windows.net/path`.
- Role mínima no storage para o MI: **Storage Blob Data Contributor** (ou Storage Blob
  Delegator + Contributor no container). File events adicionam Storage Queue Data
  Contributor, Storage Account Contributor e EventGrid EventSubscription Contributor (RG).
- Quem cria o connector: Contributor/Owner no RG; quem concede roles: Owner ou User Access
  Administrator no storage.
- `CREATE EXTERNAL LOCATION` exige o privilégio **no metastore e no storage credential**;
  na location: `CREATE MANAGED LOCATION`, `CREATE EXTERNAL TABLE`, `CREATE EXTERNAL VOLUME`,
  `READ FILES`, `WRITE FILES`.
- Restrições: só ADLS Gen2 com **HNS**; caminhos ASCII; containers com política de
  imutabilidade/WORM não suportados; Premium storage exige fila "Provided" para file events.
- File events ligados por default em novas locations (cache 7 dias, 2000 arquivos/s).

## Workspace bindings

- **Catalog binding**: restringe catalog a workspaces (opcionalmente read-only) e
  **sobrepõe** grants — privilégio existe, mas workspace não vinculado é negado.
- **External location/storage credential binding**: `isolation-mode ISOLATED` +
  `databricks workspace-bindings update-bindings external-location`; **não há binding
  read-only para external locations**; checado quando o privilégio é exercido; tabelas
  externas existentes não são afetadas se a location for desvinculada depois.
- Flag read-only da location pode levar até **60 min** para propagar.

## Connections e federação

`connection` (Lakehouse Federation) guarda credenciais para fontes externas e gera
**foreign catalogs**; aparece diretamente sob o metastore.

## Fatos que o Forge coleta

- Inventário de locations × credentials × access connector (MI) × conta de storage.
- Grants efetivos por principal (incluindo herança) e bindings por workspace.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/azure-managed-identities (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-adls (retrieved: 2026-10-06)
