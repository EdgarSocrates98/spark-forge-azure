---
sdd: 1
feature: POST_MIGRATION_VALIDATION
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/POST_MIGRATION_VALIDATION/plan.md
  sha256: "efd207055bde570cf36e0d2c463424620560c9fa549c96209012901a1ce5d43d"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_validate.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_validate.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_validate.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_validate.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_validate.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_validate.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_validate.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_validate.py -q", exit: 0}
claims:
  - text: "dimensoes avaliadas independentemente; row-count equal + metrica divergente = FAIL"
    evidence_ref: "tests/test_migration_validate.py::test_rowcount_equal_metric_differs_fails"
  - text: "data match + perf regression grande = functional pass + performance review/fail"
    evidence_ref: "tests/test_migration_validate.py::test_perf_regression_never_win"
  - text: "identidade de seguranca errada no target -> security validation failure"
    evidence_ref: "tests/test_migration_validate.py::test_wrong_target_identity_fails"
  - text: "resultado nunca auto-promove; acceptance exige evidence bundle"
    evidence_ref: "tests/test_migration_validate.py::test_no_auto_promotion"
---

# Build Report — POST_MIGRATION_VALIDATION

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
