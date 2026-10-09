---
sdd: 1
feature: DETACH_HARDENING
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/DETACH_HARDENING/design.md
  sha256: "88896e55d72ab77b056c1e5f6e8f39a837b6366985dd4a90e7f847c563ea539d"
tasks:
  - id: T1
    files:
      - sparkforge_azure/distribution/detach.py
    covers: [AC1, AC2, AC3, AC4]
    test:
      path: tests/test_distribution.py
      name: test_detach_cache_preserved_by_default_purged_on_flag
  - id: T2
    files:
      - sparkforge_azure/distribution/detach.py
      - sparkforge_azure/distribution/managed.py
    covers: [AC5, AC6]
    test:
      path: tests/test_host_integration.py
      name: test_detach_strips_block_preserves_user_text
  - id: T3
    files:
      - sparkforge_azure/distribution/detach.py
    covers: [AC7]
    test:
      path: tests/test_distribution.py
      name: test_detach_preserves_state_and_reattaches
  - id: T4
    files:
      - sparkforge_azure/distribution/config.py
    covers: [AC8]
    test:
      path: tests/test_distribution.py
      name: test_user_config_and_set_refuse_secret_keys
  - id: T5
    files:
      - docs/portability/DETACH.md
      - docs/reference/cli.md
    covers: [AC1]
    test:
      path: tests/test_distribution.py
      name: test_detach_preserves_state_and_reattaches
---

# DETACH_HARDENING — plan

T1 endurece os purges e o absent; T2 fecha o modo markers (já verde em W5);
T3 cobre reattach/id-preservation; T4 estende a guarda de segredo aos
carriers de config não-manifesto; T5 documenta. Sem verbo novo — `repair`
fica fora por decisão D3.
