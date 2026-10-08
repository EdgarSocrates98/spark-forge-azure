---
id: azure.fabric.workspace-identity
title: Fabric workspace identity - service principal gerenciado por workspace
domain: fabric-identity
authority: microsoft_official
sources:
  - url: https://learn.microsoft.com/en-us/fabric/security/workspace-identity
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/security/security-trusted-workspace-access
    retrieved: 2026-10-06
  - url: https://learn.microsoft.com/en-us/fabric/onelake/create-adls-shortcut
    retrieved: 2026-10-06
verified_at: 2026-10-06
versions: {}
status: VERIFIED
preview: false
related: [azure.fabric.onelake-security, azure.fabric.onelake-shortcuts, azure.entra.managed-identity]
---

# Fabric workspace identity

## O que é

Service principal **automanaged** pelo Fabric, associado a um workspace — o Fabric
provisiona, mantém e remove a identidade com o lifecycle do workspace. Não é um
usuário e não é idêntico a um Azure managed identity (embora análogo).

## Onde é usada

- **Trusted workspace access**: ADLS Gen2 / Storage com firewall pode aceitar tráfego
  do workspace identity via "trusted access" — sem SAS, sem access key, sem IP
  allowlist.
- **Shortcuts**: um ADLS Gen2 (e outros externos) pode ser autenticado via workspace
  identity (delegated mode) — a workspace identity é a *effective identity*, não o
  caller.
- **Connections**: algumas pipelines/integrations podem usar workspace identity em
  vez de service principal.

## Requisitos

- Requer **F-SKU** capacity ativa. Workspace em Trial/Shared não tem workspace
  identity.
- A identidade pertence ao workspace — não pode ser usada fora dele.

## Diagnóstico

- `fabric.workspace_identity` fact: evidência de que o workspace tem uma identidade
  gerenciada (Fabric controla o lifecycle).
- Delegated shortcut via workspace identity → effective identity é a identidade do
  workspace, não a do caller. O caller só precisa de permissão *no shortcut*.
- Never persist credentials, tokens, connection strings — a workspace identity não
  tem segredo para o usuário final; é gerida pelo Fabric.
- Missing workspace identity in artifacts = `unresolved` (não assumir absent).

## Cadeia de identidade no diagnóstico

| Modo do shortcut | Caller autoriza | Effective identity no target |
|---|---|---|
| passthrough | caller → shortcut → target role | o próprio caller |
| delegated (connection) | caller → shortcut → connection | identity da connection |
| delegated (workspace identity) | caller → shortcut → workspace | `fabric.workspace_identity` |

O diagnóstico nunca colapsa caller e effective identity: autorização no lakehouse
*source* não implica autorização no *target* (confused deputy).

## Evidências

- `fabric.workspace_identity` fact por workspace (principal_id exposto pelo Fabric).
- `fabric.shortcut` com `workspace_identity: true` em `auth` marca o modo delegated
  via identidade do workspace.
- `fabric.connection` com `last_test`/`authorized` é a evidência de alcance do
  target — ausência = `unresolved`, nunca allow implícito.

## Fontes

- https://learn.microsoft.com/en-us/fabric/security/workspace-identity (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/security/security-trusted-workspace-access (retrieved: 2026-10-06)
- https://learn.microsoft.com/en-us/fabric/onelake/create-adls-shortcut (retrieved: 2026-10-06)
