---
sdd: 1
feature: INSTALL_EVALS_SURFACE
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/INSTALL_EVALS_SURFACE/plan.md
  sha256: "f9a0f89a02c483eb85901f4472b28436916e833025a7f3718c91b03ea6cc675b"
tasks:
  - id: T1
    status: done
    red: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 0}
  - id: T4
    status: done
    red: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 0}
  - id: T5
    status: done
    red: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_evals_surface.py -q", exit: 0}
claims:
  - text: "9 suites classificadas nas 4 categorias §7.1 (developer=4, runtime-decision=1, output-verification=1, host-conformance=3), todas com ambiente declarado"
    evidence_ref: "tests/test_evals_surface.py::test_the_four_categories_are_all_populated"
  - text: "manifesto persiste eval_suites no shape fechado (id,kind,command) + capabilities.evals.detail; validate_manifest vazio"
    evidence_ref: "tests/test_evals_surface.py::test_manifest_eval_suites_are_classified"
  - text: "os 6 ops §7.2 são discovery.commands nomeados; discovery.ops do §6.2 continua fechado"
    evidence_ref: "tests/test_evals_surface.py::test_manifest_declares_the_7_2_ops_as_commands"
  - text: "gabarito selado não vaza: fatias de expected/ e baselines/ ausentes de describe, list, manifesto e resultado de run"
    evidence_ref: "tests/test_evals_surface.py::test_describe_never_echoes_sealed_answers"
  - text: "suites de host recusam EVALS-REQUIRES-HOST e corpus recusa EVALS-RUNNER-UNAVAILABLE — sem pass sintético"
    evidence_ref: "tests/test_evals_surface.py::test_evals_run_refuses_suites_that_only_a_host_executes"
  - text: "runners determinísticos executam e marcam environment=deterministic, real_environment_proof=false"
    evidence_ref: "tests/test_evals_surface.py::test_evals_run_agent_runtime_recomputes_cases"
  - text: "verification.plan/run invocáveis: `lab plan`/`lab verify` existem e `--help` responde"
    evidence_ref: "tests/test_evals_surface.py::test_cli_verification_ops_exist"
---

# Build report — INSTALL_EVALS_SURFACE
