---
sdd: 1
feature: PORTABLE_DISTRIBUTION
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABLE_DISTRIBUTION/design.md
  sha256: "64dd477fd0a9322ccbea29c1c94c720077753d1ca9cf337ab5e2b984dd3147cc"
tasks:
  - id: T1
    files:
      - sparkforge_azure/distribution/errors.py
      - sparkforge_azure/distribution/discovery.py
      - sparkforge_azure/distribution/paths.py
      - sparkforge_azure/distribution/config.py
    covers: [AC1, AC6, AC9]
    test:
      path: tests/test_distribution.py
      name: test_config_precedence_and_sources
  - id: T2
    files:
      - sparkforge_azure/distribution/manifests.py
      - sparkforge_azure/distribution/assets.py
      - sparkforge_azure/distribution/hosts.py
    covers: [AC2, AC7, AC8]
    test:
      path: tests/test_distribution.py
      name: test_manifest_refuses_secret_like_keys
  - id: T3
    files:
      - sparkforge_azure/distribution/managed.py
      - sparkforge_azure/distribution/service.py
    covers: [AC1, AC2, AC3, AC4]
    test:
      path: tests/test_distribution.py
      name: test_init_writes_identity_and_mcp
  - id: T4
    files:
      - sparkforge_azure/distribution/detach.py
      - sparkforge_azure/distribution/service.py
    covers: [AC5]
    test:
      path: tests/test_distribution.py
      name: test_detach_preserves_state_and_reattaches
  - id: T5
    files:
      - sparkforge_azure/cli/cmd_distribution.py
      - sparkforge_azure/cli/main.py
      - sparkforge_azure/distribution/__init__.py
      - docs/reference/cli.md
      - docs/surface.lock.json
      - tests/test_architecture_layers.py
    covers: [AC1, AC2, AC3, AC4, AC5]
    test:
      path: tests/test_distribution.py
      name: test_inspect_uninitialized_is_ok
---

# PORTABLE_DISTRIBUTION — plan

Ordem real de construção: folhas (errors/discovery/paths/config) → manifests
+ assets + hosts → managed + service → detach → superfície CLI + docs + lock.
Cada camada só importa o que já existe abaixo dela.
