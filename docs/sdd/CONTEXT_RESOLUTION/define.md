---
sdd: 1
feature: CONTEXT_RESOLUTION
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/CONTEXT_RESOLUTION/explore.md
  sha256: "ca61f410850f4fe18582c671149f42a541fb7120761f9200eb239c6a903a186d"
hypothesis:
  claim: "`context resolve` compõe reachable + scan_repository + TokenSave e
    responde o contexto relevante por escopo declarado — sem ler o workspace
    inteiro, sem cruzar fronteira de projeto, com recibo de bytes"
  prediction: "scopes selecionam exatamente os projetos declarados;
    --task materializa contexto confinado com bytes_read/bytes_avoided no
    recibo; ciclos e alvos desconhecidos recusam por nome"
  experiment: pytest tests/test_context_resolve.py — scopes, task, receipt,
    recusas, §64
acceptance:
  - id: AC1
    statement: "scope `target` (default) seleciona só o target —
      considered lista todos os declarados, stray undeclared nunca entra"
    verified_by:
      kind: test
      ref: tests/test_context_resolve.py::test_target_scope_only_reads_target
  - id: AC2
    statement: "`direct` adiciona apenas arestas diretas declaradas"
    verified_by:
      kind: test
      ref: tests/test_context_resolve.py::test_direct_scope_adds_declared_edges
  - id: AC3
    statement: "`all` é explícito e cobre todo projeto declarado — sibling
      não declarado nunca aparece (§64)"
    verified_by:
      kind: test
      ref: tests/test_context_resolve.py::test_all_scope_is_explicit
  - id: AC4
    statement: "--task materializa contexto por projeto com
      files_materialized/bytes_read no recibo persistido
      (receipt-context.json carrega project_id+workspace_id+scope)"
    verified_by:
      kind: test
      ref: tests/test_context_resolve.py::test_task_engages_ladder_with_bytes_accounting
  - id: AC5
    statement: "sem workspace.yaml recusa `workspace_not_found`; scope ou
      target desconhecido recusam `config_invalid`/`workspace_not_found`"
    verified_by:
      kind: test
      ref: tests/test_context_resolve.py::test_no_workspace_refuses
  - id: AC6
    statement: "workspace com ciclo recusa `dependency_cycle` — nunca
      recursão infinita"
    verified_by:
      kind: test
      ref: tests/test_context_resolve.py::test_dependency_cycle_refuses
success:
  - id: SC1
    metric: "0 arquivos lidos fora das raízes dos projetos selecionados
      (TokenSave confinado por resolve_within)"
    source: sparkforge_azure/distribution/context.py + tokensave/engine.py
out_of_scope:
  - merge de packs entre projetos para um único prompt — quem consome
    (agente/RoleContextPlan) decide a composição (§161–§163)
  - índice CodeIntel cross-repo — §61 pede por-project_id, já namespaced na W3
  - ranking semântico — L4 declarado indisponível offline por design
change_kinds:
  - tool_or_verb
---

# CONTEXT_RESOLUTION — define

## Contrato do verbo

`sparkforge-azure context resolve --target <id|path> --scope <s> [--task T]
[--profile P]`:

1. Descobre `workspace.yaml` (recusa `workspace_not_found`).
2. Resolve target (id, path, ou `default_target`).
3. `reachable(ws, target, scope)` → conjunto selecionado.
4. Por projeto: scan bounded + (com `--task`) escada TokenSave confinada.
5. Recibo §58 persistido + emitido.

`stop_reason` agrega: `sufficient` (toda escada parou em STOP_SUFFICIENT),
`partial` (budget/no-gain/unresolved), `scope_complete` (sem task).
