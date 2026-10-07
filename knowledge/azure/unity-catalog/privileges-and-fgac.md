---
id: azure.unity-catalog.privileges-and-fgac
title: Unity Catalog - privilégios, row filters, column masks e ABAC
domain: unity-catalog
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/filters-and-masks/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/databricks/tables/features/change-data-feed
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {dbr: ["12.2 LTS+", "15.4 LTS+", "16.3+"]}
status: VERIFIED
preview: false
related: [azure.unity-catalog.securable-model, governance.multi-layer-conflicts, azure.purview.unified-catalog-and-lineage]
---

# Unity Catalog — privilégios e fine-grained access control

## Privilégios essenciais

| Objeto | Privilégios típicos |
|---|---|
| Catalog | `USE CATALOG`, `BROWSE` (só catalog), `CREATE SCHEMA` |
| Schema | `USE SCHEMA`, `CREATE TABLE`, `CREATE VOLUME`, `CREATE FUNCTION`, `CREATE MODEL` |
| Table/View | `SELECT`, `MODIFY` |
| Volume | `READ VOLUME`, `WRITE VOLUME` |
| Function/Model | `EXECUTE` |
| External location | `READ FILES`, `WRITE FILES`, `CREATE EXTERNAL TABLE`, `CREATE EXTERNAL VOLUME`, `CREATE MANAGED LOCATION` |
| Storage credential | `CREATE EXTERNAL LOCATION` (também no metastore) |

- Privilégios DML finos (`INSERT`/`UPDATE`/`DELETE` separados) estão em **Beta** (PREVIEW).
- Erro comum documentado: conceder `WRITE FILES` sem `READ FILES` na external location
  resulta em `PERMISSION_DENIED`; conceder os dois.
- Herança: catalog → schema → objetos. Metastore não herda.
- Workspace-catalog binding sobrepõe qualquer grant.

## Row filters e column masks (por tabela)

- Implementados como **SQL UDFs** aplicadas à tabela; GA (sem rótulo de preview).
- Requisitos/limitações documentados:
  - DBR **12.2 LTS+**;
  - não aplicáveis a views;
  - sem acesso via Iceberg REST / Unity REST;
  - sem time travel e sem clones na tabela filtrada;
  - compute **dedicated** precisa de DBR **15.4+** com serverless (FGAC) para ler;
    escritas exigem **16.3+**.
- Automatic CDF **não** é suportado em tabelas com row filters/column masks.

## ABAC (attribute-based access control)

- Políticas baseadas em **governed tags**, definidas em catalog/schema/table
  (nível de metastore = **Beta**).
- Tipos: row filter policies, column mask policies, **GRANT policies**; **DENY policies =
  Beta**; ABAC com time travel = **Beta**.
- Recomendado pela Databricks em vez de filtros/máscaras por tabela.
- Status: políticas centrais aparentam GA; subfeatures citadas acima são Beta (PREVIEW).

## Ordem de diagnóstico de "acesso negado" em dados UC

1. Workspace está vinculado ao catalog? (binding)
2. `USE CATALOG` + `USE SCHEMA` presentes (direto ou por grupo)?
3. Privilégio no objeto (`SELECT`/`MODIFY`/`READ VOLUME`…)?
4. Row filter/column mask/ABAC alterando o resultado (vazio ≠ negado)?
5. Se external: cadeia de storage (ver `azure.unity-catalog.troubleshooting-external-locations`).

## Armadilhas

- Resultado vazio por row filter parece "sem dados" — não é erro de permissão.
- Owner de objeto tem todos os privilégios; transferir ownership muda o comportamento.
- Grupos de workspace local vs grupos de account: privilégios UC usam principals de account
  (não relido aqui — UNVERIFIED).

## Não verificado

- Lista completa de privilégios por securable (só os citados nas páginas lidas).
- Comportamento de grupos workspace-local em grants UC.

## Fontes

- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/filters-and-masks/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/abac/ (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/databricks/tables/features/change-data-feed (retrieved: 2026-10-06)
