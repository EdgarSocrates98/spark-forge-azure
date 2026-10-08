---
sdd: 1
feature: MIGRATION_COMPATIBILITY
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/MIGRATION_COMPATIBILITY/plan.md
  sha256: "8841d5af32bbb289b3566ae74c9207f6f5f3e76988711d3333d6ef22dd0b6da8"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_compat.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_compat.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_compat.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_compat.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_compat.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_compat.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd .tmp-mig-red && python -m pytest tests/test_migration_compat.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_migration_compat.py -q", exit: 0}
claims:
  - text: "toda dimensao avaliada retorna status do vocabulario fechado + evidence"
    evidence_ref: "tests/test_migration_compat.py::test_dimensions_closed_vocabulary"
  - text: "unsupported/explicit > review; ausencia de evidencia e unknown, nao compatible"
    evidence_ref: "tests/test_migration_compat.py::test_absence_is_unknown_not_compatible"
  - text: "score, se existir, e auxiliar e nunca esconde blockers/unknowns/refactors"
    evidence_ref: "tests/test_migration_compat.py::test_score_never_hides_blockers"
  - text: "conflito oficial-vs-Forge vira REVIEW com provenance, nunca override silencioso"
    evidence_ref: "tests/test_migration_compat.py::test_official_conflict_is_review"
---

# Build Report — MIGRATION_COMPATIBILITY

Red em worktree `.tmp-mig-red` @ `61367a5` (pre-Cycle-5): testes copiados falham com ModuleNotFoundError (exit 2); green em `feat/cycle5-migration`.
