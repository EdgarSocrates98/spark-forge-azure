---
id: azure.purview.unified-catalog-and-lineage
title: Microsoft Purview - Unified Catalog, Data Map, lineage e conector Unity Catalog
domain: azure-purview
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/purview/unified-catalog
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/purview/data-gov-classic-lineage
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/purview/register-scan-azure-databricks-unity-catalog
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.unity-catalog.securable-model, governance.multi-layer-conflicts, azure.fabric.onelake-shortcuts, azure.databricks.workflows]
---

# Microsoft Purview — catálogo e lineage

## Camadas

- **Data Map**: camada de scan e metadados (sources, scans, classificações, lineage).
- **Unified Catalog**: governance domains, data products, glossary terms, critical data
  elements, OKRs, data quality, health controls/actions, políticas de acesso self-service.
  Rollout regional; exige **upgrade enterprise** da nova experiência Purview.
- Lineage clássico: lineage de entidade e de **coluna**, com status de execução.

## Conector Azure Databricks Unity Catalog

| | "Azure Databricks Unity Catalog" (novo) | "Azure Databricks" (antigo) |
|---|---|---|
| Escopo | UC | Hive metastore + UC |
| Scan | incremental; **sem scoped scan** | scoped scan |
| Auth | service principal, system-assigned MI, PAT | — |
| Rede | managed VNet IR suportado | — |

- Metadados: metastore, catalog, schema, table, view, colunas, tags.
- **Lineage só de execuções de notebook**; requer acesso a `system.access` + `SELECT` em
  `system.access.table_lineage` e `system.access.column_lineage`.
- Column lineage vem de **clusters**, não de SQL warehouses.
- Tabelas externas: só metadados.
- Lineage de Databricks disparado por **ADF não aparece**.
- Sem lineage na região China.
- Escopo de scan em modo avançado: **PREVIEW**.

## Fabric

- Governança nativa do Fabric = **OneLake catalog** (descoberta, insights, domains,
  endorsement, lineage).
- Purview acrescenta Information Protection, DLP, Audit, Insider Risk e governança de
  Copilot/agentes.

## Rede

- Private DNS zones: `privatelink.purview.azure.com` (account),
  `privatelink.purviewstudio.azure.com` (portal), `privatelink.purview-service.microsoft.com`
  (platform).

## SDKs (PyPI, 2026-10-06)

- `azure-purview-datamap` 1.0.0b2 (abr/2025; Data Map atual) — beta.
- `azure-purview-catalog` 1.0.0b4 (2022); `account`/`administration`/`scanning`: betas de
  2021 (estagnados). Coletor do Forge deve tratar a API como instável.

## Relação com Unity Catalog (não 1:1)

- UC **aplica** acesso a dados no Databricks; Purview **cataloga e classifica** — não
  concede SELECT em tabelas UC. Ver `governance.multi-layer-conflicts`.

## O que NÃO afirmar

- Que lineage Purview é completo para Databricks (jobs ADF, SQL warehouses e tabelas
  externas têm lacunas documentadas).

## Não verificado

- Páginas de lineage Purview para ADF/Synapse (não lidas).

## Fontes

- https://learn.microsoft.com/en-us/purview/unified-catalog (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/purview/data-gov-classic-lineage (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/purview/register-scan-azure-databricks-unity-catalog (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns (retrieved: 2026-10-06)
