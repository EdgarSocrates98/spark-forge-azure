---
sdd: 1
feature: FORGE_PORTAL
phase: plan
profile: dev
status: ready
upstream:
  sha256: "0327ebac3324163b133763f6e85da1a8ccf94eacd45cc70b42c022860d1d1451"
  path: docs/sdd/FORGE_PORTAL/design.md
tasks:
  - id: T1
    files:
      - sparkforge_azure/_forge_portal.py
      - portal/assets/
    covers: [AC2, AC8]
    test:
      path: tests/test_portal_adapter.py
      name: test_bootstrap_exige_sessao
  - id: T2
    files:
      - sparkforge_azure/portal_adapter.py
    covers: [AC1, AC3, AC4, AC5, AC6]
    test:
      path: tests/test_portal_adapter.py
      name: test_install_plan_apply_verified
  - id: T3
    files:
      - sparkforge_azure/cli/cmd_portal.py
      - sparkforge_azure/cli/main.py
      - docs/surface.lock.json
    covers: [AC7]
    test:
      path: tests/test_portal_adapter.py
      name: test_portal_verb_parseia
  - id: T4
    files:
      - pyproject.toml
    covers: [AC8]
    test:
      path: tests/test_portal_adapter.py
      name: test_assets_index_resolvido
  - id: T5
    files:
      - tests/test_portal_adapter.py
      - tests/test_architecture_layers.py
      - docs/reference/cli.md
    covers: [AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8]
    test:
      path: tests/test_portal_adapter.py
      name: test_catalogo_skills_e_agents_do_repo
---

# FORGE_PORTAL — plan

Vendor primeiro (T1), adapter depois (T2), superfície CLI (T3),
packaging (T4), testes + docs + camadas por último (T5).
