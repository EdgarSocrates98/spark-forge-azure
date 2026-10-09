---
sdd: 1
feature: PORTABILITY_CLOSURE_POLISH
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABILITY_CLOSURE_POLISH/design.md
  sha256: "8b8304c3d7f1a0cb2b3d5733169f31e7497ac45e920a4136affe89914dde6230"
tasks:
  - id: T1
    files:
      - scripts/gen_current_state.py
      - docs/CURRENT_STATE.md
    covers: [AC1]
    test:
      path: tests/test_portability_evals.py
      name: test_portability_gate_static_ok
  - id: T2
    files:
      - scripts/check_portability.py
    covers: [AC3]
    test:
      path: tests/test_portability_evals.py
      name: test_portability_gate_static_ok
  - id: T3
    files:
      - docs/portability/PORTABILITY_OUTCOME.md
      - docs/portability/PORTABILITY_AUDIT.md
      - docs/portability/WORKSPACES.md
      - docs/README.md
    covers: [AC2]
    test:
      path: tests/test_portability_evals.py
      name: test_portability_gate_static_ok
  - id: T4
    files:
      - tests/test_distribution.py
    covers: [AC4]
    test:
      path: tests/test_distribution.py
      name: test_existing_verbs_work_without_distribution_init
---

# PORTABILITY_CLOSURE_POLISH — plan

T1 generator + doc primeiro (estado medido deriva de fontes vivas). T2
estende o gate existente — kinds ⊆ troubleshooting, quickstart ⊆ surface
lock, CURRENT_STATE fresco. T3 reescreve só a parte *atual* da paridade —
snapshot de closure preservado. T4 prova backward compat. Claims stamp por
último, depois de todos os gates verdes (§106).
