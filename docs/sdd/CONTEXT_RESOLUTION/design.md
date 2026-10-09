---
sdd: 1
feature: CONTEXT_RESOLUTION
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/CONTEXT_RESOLUTION/define.md
  sha256: "4691c3bbc717101a7d1ba6ef796c9abaa8f43cc3b55ee1fcd900ba8519e1a9a9"
files:
  - path: sparkforge_azure/distribution/context.py
    action: create
    reason: "context_resolve — orquestra reachable + scan_repository +
      TokenSave por projeto; recibo §58 via write_atomic"
  - path: sparkforge_azure/cli/cmd_context.py
    action: create
    reason: "verbo `context resolve` — refused_document em PortableError"
  - path: sparkforge_azure/cli/main.py
    action: modify
    reason: "registrar cmd_context em COMMAND_MODULES"
  - path: tests/test_context_resolve.py
    action: create
    reason: "AC1–AC6 — scopes, task, recibo, recusas, ciclo"
  - path: tests/test_architecture_layers.py
    action: modify
    reason: "declarar arestas distribution→{paths,tokensave}"
  - path: docs/reference/cli.md
    action: modify
    reason: "seção `context resolve` (gate docs_surface)"
  - path: docs/surface.lock.json
    action: modify
    reason: regen com o verbo novo
  - path: docs/portability/CONTEXT_RESOLUTION.md
    action: create
    reason: "doc do modelo — scopes, §64, economia, recibo"
  - path: docs/README.md
    action: modify
    reason: indexar CONTEXT_RESOLUTION.md
decisions:
  - id: D1
    choice: "Um TokenSave por projeto, confinado a `resolve_within(root)` —
      §64 vira invariante estrutural: um projeto não *pode* ler arquivo de
      outro, em vez de depender de disciplina."
    rejected:
      - "TokenSave único na raiz do workspace — mistura fronteiras e leria
        undeclared siblings (o scan bounded do root não conhece declarações)"
      - "filtro pós-leitura por path — o arquivo já foi lido; a confiança
        precisa estar no confinamento, não no descarte"
    rollback: "context_resolve é read+receipt; trocar a estratégia não migra
      estado"
  - id: D2
    choice: "`--task` separa resolução de materialização. Sem task o verbo
      responde o conjunto + contagem — o barato determinístico; com task
      roda a escada com o profile escolhido."
    rejected:
      - "sempre materializar — gastaria bytes em todo projeto selecionado
        mesmo quando a pergunta é só 'quem está no escopo'"
      - "flag --materialize separada — task já implica materialização; um
        eixo a menos na superfície"
    rollback: "default target-only já é o barato; nada a desfazer"
  - id: D3
    choice: "Índice e cache por projeto via helpers W3
      (`codeintel_db`/`project_cache_dir` com paths re-resolvidos por root
      de projeto) — honra §61–§63 tanto no layout clássico quanto em roots
      env-compartilhados."
    rejected:
      - "índice único no workspace root — viola §61 (indexar por
        project_id) e mistura namespaces"
    rollback: "paths são derivados, não gravados — mudar a política não
      migra índices"
covers:
  - part: sparkforge_azure/distribution/context.py (context_resolve)
    acceptance: [AC1, AC2, AC3, AC4, AC5, AC6]
  - part: sparkforge_azure/distribution/workspace.py (reachable)
    acceptance: [AC1, AC2, AC3, AC6]
  - part: sparkforge_azure/cli/cmd_context.py
    acceptance: [AC1, AC4, AC5]
---

# CONTEXT_RESOLUTION — design

## Fluxo

```
resolve_paths(cwd) → discover → workspace.yaml (refuse ws_not_found)
→ _resolve_target(id|path|default_target)
→ reachable(ws, target, scope)  (cycles → dependency_cycle)
→ por projeto selecionado (ordenado):
     resolve_declared_path → is_dir? senão unresolved
     scan_repository(root) → files_considered / bytes scanned
     [--task] TokenSave(root, profile, index_db=codeintel_db,
                        cache_dir=ns).context(task)
→ receipt {target, scope, considered, selected, files, bytes, stop_reason}
→ write_atomic → <state>/receipt-context.json
```

## Determinismo

`reachable` retorna ids (ordenação aplicada no resolve); scan_repository é
sorted-scandir; ledger conta bytes — mesma entrada, mesma saída.

## Compatibilidade

Nenhum comportamento existente muda: `tokensave context` continua o verbo
por-raiz; `context resolve` é o orquestrador workspace-level.
