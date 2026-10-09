---
sdd: 1
feature: RELOCATABLE_IDENTITY
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/RELOCATABLE_IDENTITY/design.md
  sha256: "7055cdb041e07fb040f3432edf76269353a8fccde546da1c3e5840fef98d5ce3"
tasks:
  - id: T1
    files:
      - sparkforge_azure/distribution/identity.py
    covers: [AC5, AC6]
    test:
      path: tests/test_relocatable_identity.py
      name: test_state_namespace_isolation
  - id: T2
    files:
      - sparkforge_azure/distribution/workspace.py
    covers: [AC2, AC3, AC4]
    test:
      path: tests/test_relocatable_identity.py
      name: test_copy_is_identity_collision_not_merge
  - id: T3
    files:
      - sparkforge_azure/distribution/service.py
    covers: [AC1, AC6]
    test:
      path: tests/test_relocatable_identity.py
      name: test_init_receipt_carries_workspace_id
  - id: T4
    files:
      - docs/portability/PORTABLE_DISTRIBUTION.md
      - docs/portability/WORKSPACES.md
    covers: [AC1, AC2, AC3, AC4, AC5, AC6]
    test:
      path: tests/test_relocatable_identity.py
      name: test_project_id_survives_move
---

# RELOCATABLE_IDENTITY — plan

`identity.py` primeiro (puro, leaf), depois a política de `workspace_add`,
depois `service` (receipt/inspect), por último docs.

## Pontos não-óbvios

- **Detecção "compartilhado"**: `paths.env_overrides` marca quais roots
  vieram de env — o helper consulta isso em vez de re-ler `os.environ`,
  mantendo determinismo e testes com `env=` injetado.
- **Receipt duplo**: `workspace init` não grava `receipt-distribution.json`
  — quem grava é `distribution init`; o teste chama os dois nessa ordem.
- **Falso positivo aceitável**: stub vazio no path antigo classifica como
  cópia (bloqueia add). Barato, explícito, reviewável — melhor que fundir
  identidades.
