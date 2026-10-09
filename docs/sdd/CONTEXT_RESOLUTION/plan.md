---
sdd: 1
feature: CONTEXT_RESOLUTION
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/CONTEXT_RESOLUTION/design.md
  sha256: "4fd99a8a6ad0a55a1f9d725e75db0a0d86c5ab84414680e1bff38695a812c695"
tasks:
  - id: T1
    files:
      - sparkforge_azure/distribution/context.py
    covers: [AC1, AC2, AC3, AC4, AC5, AC6]
    test:
      path: tests/test_context_resolve.py
      name: test_target_scope_only_reads_target
  - id: T2
    files:
      - sparkforge_azure/cli/cmd_context.py
      - sparkforge_azure/cli/main.py
      - docs/reference/cli.md
      - docs/surface.lock.json
    covers: [AC1, AC4, AC5]
    test:
      path: tests/test_context_resolve.py
      name: test_task_engages_ladder_with_bytes_accounting
  - id: T3
    files:
      - tests/test_architecture_layers.py
      - docs/portability/CONTEXT_RESOLUTION.md
      - docs/README.md
    covers: [AC3, AC6]
    test:
      path: tests/test_context_resolve.py
      name: test_all_scope_is_explicit
---

# CONTEXT_RESOLUTION — plan

Serviço primeiro (T1), superfície + lock (T2), doc + bordas (T3).

## Pontos não-óbvios

- `ContextResult.levels_used` (não `levels`) — campo real do dataclass.
- `WorkspaceDecl` não carrega `root` — vem de `Discovery.workspace_root`.
- `_resolve_target` aceita id ou path resolvido; nome não é parte do
  `ProjectDecl` — `--target` por nome seria ambíguo, então não é aceito.
- Recibo vai para o state dir *do chamador* (cwd do resolve), não de um
  projeto selecionado — quem pediu o contexto guarda a prova.
