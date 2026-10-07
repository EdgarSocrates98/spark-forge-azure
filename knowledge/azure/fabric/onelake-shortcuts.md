---
id: azure.fabric.onelake-shortcuts
title: OneLake shortcuts - tipos, identidade, cache e limites
domain: fabric-onelake
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.fabric.data-engineering-spark, azure.adls.gen2, lakehouse.iceberg, governance.multi-layer-conflicts, migration.aws-to-azure-concepts]
---

# OneLake shortcuts

## O que são

Objetos no OneLake que apontam para outro local (**target path**), aparecendo como pasta
no **shortcut path**. Funcionam como links simbólicos: apagar o shortcut não apaga o
alvo; mover/renomear/apagar o alvo quebra o shortcut.

## Onde criar

- **Lakehouse / Tables**: só no **nível superior** (sem subpastas). Se o alvo é Delta, a
  tabela é descoberta e o schema sincronizado automaticamente. Pode apontar para uma
  tabela ou para um **schema** (só em lakehouse com schemas).
- **Lakehouse / Files**: em qualquer nível; sem descoberta de tabela; qualquer formato.
- **KQL database**: pasta Shortcuts, consultada com `external_table()`.
- Eventhouse: database shortcuts com seleção de subitens.
- Criação via portal ou REST API (`/rest/api/fabric/core/onelake-shortcuts`).

## Tipos de alvo

| Interno (OneLake) | Externo |
|---|---|
| lakehouses, warehouses, KQL DBs, SQL DBs, mirrored DBs, mirrored Azure Databricks catalogs, semantic models | ADLS Gen2, Azure Blob, Amazon S3, S3-compatible, Google Cloud Storage, Dataverse, Iceberg, OneDrive/SharePoint |

Locais on-premises/rede restrita: via on-premises data gateway (OPDG).

## Identidade e autorização

- **Internos**: OneLake usa a **identidade do usuário chamador**; ele precisa de permissão
  no alvo.
- Exceção: Power BI semantic model em **Direct Lake over SQL** ou T-SQL em **Delegated
  identity mode** passa a identidade do **dono do item** chamador, não do usuário. Para
  passthrough, usar Direct Lake over OneLake ou T-SQL em User identity mode.
- **Externos (ADLS, S3)**: autorização delegada por **cloud connection**; criar shortcut é
  um *bind* e exige permissão na connection.
- Apagar arquivo **dentro** de um shortcut apaga no alvo se o usuário tem escrita lá
  (sem cascade ao apagar o shortcut em si).

## Cache

- Para GCS, S3, S3-compatible e shortcuts via OPDG; retenção configurável de 1 a 28 dias
  por workspace; arquivos > 1 GB não são cacheados; reduz egress cross-cloud.

## Limites

- 100.000 shortcuts por item Fabric.
- 100 connections únicas de shortcuts externos por item.
- 10 shortcuts por caminho OneLake; no máximo 5 shortcuts encadeados.
- Nomes/caminhos sem `%` ou `+`; sem caracteres não latinos; nome com espaço não vira
  tabela Delta.
- Table API pode levar até 1 min para reconhecer shortcut novo.
- Lineage de shortcuts para warehouses e semantic models não disponível.

## Acesso por engines

- Spark: caminho relativo (`Tables/MyShortcut`) ou SQL (`MyLakehouse.MyShortcut`).
- SQL analytics endpoint: só shortcuts Delta em Tables.
- Fora do Fabric: API OneLake (subconjunto de ADLS Gen2/Blob), ex.
  `https://onelake.dfs.fabric.microsoft.com/<workspace>/<item>/Tables/...`.

## Conflitos típicos (para governança)

- Usuário vê o shortcut mas recebe negação: falta permissão no **alvo** (interno) ou na
  **connection** (externo) — ver `governance.multi-layer-conflicts`.
- Relatório Direct Lake over SQL mostra dados que o usuário não poderia ler diretamente:
  identidade delegada do dono.

## Fontes

- https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric (retrieved: 2026-10-06)
