---
sdd: 1
feature: DATA_ONELAKE
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/DATA_ONELAKE/plan.md
  sha256: "980b51988fe59c3d0d0028afc51729b0512bfd22abcd37a82bfaeb3cbff37ecd"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_data.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_data.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_data.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_data.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_data.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_data.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_data.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_data.py -q", exit: 0}
claims:
  - text: "recommendation e uma de retain/shortcut/copy/hybrid com dims de decisao (formato/retirement/egress/latency)"
    evidence_ref: "tests/test_migration_data.py::test_strategy_closed_set_with_evidence"
  - text: "Delta elegivel vira shortcut candidate mas nunca recomendacao forcada"
    evidence_ref: "tests/test_migration_data.py::test_delta_shortcut_candidate_not_forced"
  - text: "retirement da fonte pende para copy quando evidencia suporta"
    evidence_ref: "tests/test_migration_data.py::test_retirement_prefers_copy"
  - text: "managed vs external tables + HMS sao avaliados separadamente"
    evidence_ref: "tests/test_migration_data.py::test_hms_managed_external_split"
---

# Build Report — DATA_ONELAKE

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
