---
sdd: 1
feature: PORTABLE_INSTALL_LIFECYCLE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/PORTABLE_INSTALL_LIFECYCLE/design.md
  sha256: "098b9badebecb6b9a16daf13e6f2d54aa5bc2e2d1a0239b0f9ca059a51e2158b"
tasks:
  - id: T1
    files: [sparkforge_azure/_installkit.py, pyproject.toml]
    covers: [AC1]
    test: {path: tests/test_install_lifecycle.py, name: test_dry_run_plans_and_writes_nothing}
  - id: T2
    files: [sparkforge_azure/install/service.py, sparkforge_azure/install/__init__.py]
    covers: [AC1, AC2, AC3, AC5, AC6, AC7]
    test: {path: tests/test_install_lifecycle.py, name: test_install_apply_writes_managed_assets}
  - id: T3
    files: [sparkforge_azure/install/service.py]
    covers: [AC4]
    test: {path: tests/test_install_lifecycle.py, name: test_status_and_doctor_health_schema}
  - id: T4
    files: [sparkforge_azure/cli/cmd_install.py, sparkforge_azure/cli/main.py, docs/reference/cli.md, docs/surface.lock.json]
    covers: [AC8]
    test: {path: tests/test_install_lifecycle.py, name: test_cli_dispatches_all_verbs}
---

# Plan — PORTABLE_INSTALL_LIFECYCLE

T1 vendors o engine; T2 o serviço (apply/status/doctor/repair/uninstall/
update + escopo user); T3 a saúde forge/*; T4 a superfície CLI e os
locks de docs/surface que a acompanham.
