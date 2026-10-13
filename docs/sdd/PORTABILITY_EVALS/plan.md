---
sdd: 1
feature: PORTABILITY_EVALS
phase: plan
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABILITY_EVALS/design.md
  sha256: "4f4b14f213cfa2a3c5fc13cb5e01d71f441d95a11904ee0b9aed3e747abaf555"
tasks:
  - id: T1
    files:
      - evals/portability/suite.yaml
      - evals/portability/runner.py
      - tests/test_portability_evals.py
    covers: [AC1]
    test:
      path: tests/test_portability_evals.py
      name: test_portability_matrix_all_cases_ok
  - id: T2
    files:
      - scripts/check_portability.py
      - tests/test_portability_evals.py
    covers: [AC2, AC3]
    test:
      path: tests/test_portability_evals.py
      name: test_portability_gate_static_ok
  - id: T3
    files:
      - docs/portability/PORTABILITY_OUTCOME.md
      - docs/guides/SPARKFORGE_AZURE_PORTABLE.md
      - docs/guides/SPARKFORGE_AZURE_PORTABLE.pt-BR.md
      - docs/claims.lock.json
      - docs/README.md
    covers: [AC4, AC5]
    test:
      path: tests/test_portability_evals.py
      name: test_portability_gate_static_ok
---

# PORTABILITY_EVALS — plan

T1 runner+matriz primeiro (prova §97–§101), T2 gate + wheel depois
(§187–§188, §194), T3 outcome+quickstarts+claims por último — claims só
entram depois da prova existir (§189).
