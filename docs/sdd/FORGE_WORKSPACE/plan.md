---
sdd: 1
feature: FORGE_WORKSPACE
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/FORGE_WORKSPACE/design.md
  sha256: "3da3f9927decb13273648f2b64d956ecbd63c510b124ca8f0c8e12e7ebdf9e28"
tasks:
  - id: T1
    files:
      - sparkforge_azure/distribution/workspace.py
    covers: [AC1, AC2, AC3, AC4]
    test:
      path: tests/test_forge_workspace.py
      name: test_add_monorepo_child_stores_relative
  - id: T2
    files:
      - sparkforge_azure/distribution/workspace.py
    covers: [AC5, AC6]
    test:
      path: tests/test_forge_workspace.py
      name: test_cycle_is_explicit_review_state
  - id: T3
    files:
      - sparkforge_azure/distribution/workspace.py
    covers: [AC7, AC8]
    test:
      path: tests/test_forge_workspace.py
      name: test_discover_suggests_without_writing
  - id: T4
    files:
      - sparkforge_azure/cli/cmd_workspace.py
      - sparkforge_azure/cli/main.py
      - docs/reference/cli.md
      - docs/surface.lock.json
      - docs/portability/WORKSPACES.md
    covers: [AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8]
    test:
      path: tests/test_forge_workspace.py
      name: test_workspace_roundtrip_survives_within_root_move
---

# FORGE_WORKSPACE — plan

Serviço primeiro (T1–T3), superfície depois (T4). `reachable` e
`detect_cycles` ficam prontos para o `context resolve` da W4.
