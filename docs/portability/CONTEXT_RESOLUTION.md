# CONTEXT_RESOLUTION — contexto com escopo de workspace (W4)

`sparkforge-azure context resolve` responde "qual contexto deste workspace
é relevante para este target?" **sem ler o workspace inteiro**
(prompt_evo_portable.md §48–§64). Três camadas compostas, nenhuma nova:

```
workspace.yaml → target → reachable(scope) → scan_repository → TokenSave L0→L6
```

## Scopes (§51, §54–§57)

| Scope | Conjunto | Quando |
|---|---|---|
| `target` | só o target | **default** — nunca o workspace inteiro por omissão |
| `direct` | target + arestas diretas declaradas | dependência imediata |
| `transitive` | fecho transitivo das arestas | só quando solicitado |
| `all` | todo projeto declarado | **explícito only** |

Ciclos recusam `dependency_cycle` — nunca recursão infinita.

## Segurança de contexto (§64)

Um projeto nunca recebe arquivos de outro sem aresta declarada ou `all`
explícito. É estrutural, não política: cada projeto selecionado ganha um
`TokenSave` próprio confinado por `resolve_within` à sua raiz — path
traversal para fora do projeto é impossível por construção. Projeto não
declarado no workspace nunca entra no conjunto.

## Economia (§53, §160)

- Sem `--task`: resolve apenas o *conjunto* de projetos + contagem bounded
  de arquivos (`scan_repository` já aplica deny-names e `max_file_bytes`).
- Com `--task`: a escada L0→L6 roda **por projeto** com o profile
  (`economy` default) — L5 fatiado, L6 full só em `deep`.
- Índice CodeIntel e cache resolvem pelos namespaces lógicos da W3:
  `state/projects/<project_id>/local/codeintel/graph.sqlite3` quando o
  root é env-compartilhado, senão o `.sparkforge-azure/` do próprio
  projeto. Cache key inclui `workspace_id` (§61–§63).

## Recibo (§58)

`receipt-context.json` no state dir do chamador:

```json
{
  "project_id": "sfa-…", "workspace_id": "sfw-…", "context_scope": "direct",
  "target": "sfa-…", "scope": "direct", "profile": "economy",
  "projects_considered": ["sfa-…"], "projects_selected": ["sfa-…"],
  "files_considered": 12, "files_materialized": 4,
  "bytes_read": 2048, "bytes_avoided": 31820,
  "stop_reason": "sufficient", "unresolved": []
}
```

`stop_reason` agrega o pior resultado dos projetos: `sufficient` quando
toda escada parou em `STOP_SUFFICIENT`, `partial` quando alguma parou por
budget/no-gain; `scope_complete` quando `--task` não foi pedido (resolve =
conjunto de projetos). Paths que sumiram viram `unresolved` — reportado,
nunca silencioso.

## O que não faz

- Não inferre dependências de imports — o grafo é o manifesto declarado.
- Não materializa conteúdo entre projetos — o pack é por-projeto; o
  agente que consome decide o merge (RoleContextPlan usa este resolve,
  §161–§163).
