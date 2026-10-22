---
sdd: 1
feature: INSTALL_EVALS_SURFACE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/INSTALL_EVALS_SURFACE/design.md
  sha256: "40d8ecfcc908042a2cd6cf3875f98d479be507401e81cd9ba9cd28b3cf28616e"
tasks:
  - id: T1
    files: [sparkforge_azure/evals/taxonomy.py]
    covers: [AC1, AC4]
    test: {path: tests/test_evals_surface.py, name: test_the_four_categories_are_all_populated}
  - id: T2
    files: [sparkforge_azure/evals/surface.py, sparkforge_azure/cli/cmd_evals.py, sparkforge_azure/cli/main.py]
    covers: [AC5, AC6]
    test: {path: tests/test_evals_surface.py, name: test_evals_run_agent_runtime_recomputes_cases}
  - id: T3
    files: [sparkforge_azure/discovery_ops.py, sparkforge_azure/install/service.py, sparkforge_azure/discovery.py]
    covers: [AC2, AC3, AC7]
    test: {path: tests/test_evals_surface.py, name: test_manifest_declares_the_7_2_ops_as_commands}
  - id: T4
    files: [tests/test_evals_surface.py]
    covers: [AC4, AC5]
    test: {path: tests/test_evals_surface.py, name: test_describe_never_echoes_sealed_answers}
  - id: T5
    files: [docs/evals-taxonomy.md, docs/README.md, docs/reference/cli.md, docs/surface.lock.json]
    covers: [AC3]
    test: {path: tests/test_evals_surface.py, name: test_cli_evals_list}
---

# Plan — INSTALL_EVALS_SURFACE
