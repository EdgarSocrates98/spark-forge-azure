---
id: azure.fabric.onelake-security
title: OneLake data security - roles, escopos e o modelo grant-only
domain: fabric-onelake
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/onelake/security/get-started-security
    retrieved: 2026-10-08
  - url: https://learn.microsoft.com/en-us/fabric/onelake/security/create-manage-roles
    retrieved: 2026-10-08
  - url: https://learn.microsoft.com/en-us/fabric/onelake/security/table-folder-security
    retrieved: 2026-10-08
  - url: https://learn.microsoft.com/en-us/fabric/onelake/security/data-access-control-model
    retrieved: 2026-10-08
verified_at: 2026-10-08
versions: {}
status: VERIFIED
preview: false
related: [azure.fabric.onelake-shortcuts, azure.fabric.data-engineering-spark, governance.multi-layer-conflicts]
---

# OneLake data security

## Dois planos, sempre separados

- **Control plane** (workspace + item): workspace roles (Admin/Member/Contributor/Viewer)
  e permissões de item (Read, ReadData, Write, Share, etc.) governam *management* e
  metadados. Não são a camada de dados.
- **Data plane** (OneLake security): roles dentro do item Lakehouse governam quem lê o
  quê — escopo por tabela, pasta, schema, e filtros por linha/coluna.

Diagnóstico precisa tratar os planos separadamente: "workspace permission OK" não
implica "data-plane allow".

## Roles OneLake

- **Grant-only**: OneLake security não tem role de *Deny*. Permissões: `Read`,
  `ReadWrite`, `ReadAll`, `Write`, `Reshare`, `Execute`, `Explore`, `Build`, etc.
  (escopo por item). A ausência de grant é a negação — nunca um deny explícito.
- **Escopos**: todo o item (default), `Tables/<t>` (tabela), `Files/<p>` (pasta),
  schemas (em lakehouse com schema), `RLS` por linha e `CLS` por coluna.
- **Quem define**: roles vivem no item Lakehouse (não no workspace).

## Bypass de data-plane

Principals com workspace role **Admin/Member/Contributor** já têm acesso de dados — o
check de data-plane se aplica efetivamente a **Viewer** ou principals com permissão de
item somente. Avaliar roles OneLake antes de conferir workspace role erra a ordem.

## RLS/CLS — engine-aware

- RLS e CLS são avaliados **pelo engine que serve a query** (Spark, SQL endpoint,
  KQL, Power BI), não pelo storage. Não é garantia universal: um motor que lê o
  path diretamente (abfss, atalho) pode ignorar o filtro.
- Só roles `Read` aceitam filtros. `ReadWrite` nunca pode ter RLS/CLS.
- Uma role com filtros em um motor que não os respeita é "restricting not enforced" —
  diagnóstico deve marcar isso, não afirmar que o filtro funcionou.

## Diagnóstico

- `onelake_security` layer: evidência = `onelake.security_role` fact com grant e
  escopo que cubra a tabela/pasta pedida.
- `item_permission` layer: evidência = `fabric.item` com `permissions` (ou workspace
  role que já carrega acesso implícito).
- Missing OneLake role artifact = `unresolved`, nunca allow.
- Cross-tenant: role OneLake só vale no mesmo tenant — atalho cross-tenant usa
  delegated, não passthrough.
