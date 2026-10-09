---
sdd: 1
feature: AGENT_VALUE_EVAL
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_VALUE_EVAL/define.md
  sha256: cd1fbddbc3b3d486df89ab98f34f64e408d776dde8ae9bb6316f4bf8b68131a6
files:
- path: sparkforge_azure/agentic/agent_eval.py
  action: create
  reason: harness A/B + EvalResult + value_vector + necessity
- path: evals/agent_runtime/cases/
  action: create
  reason: 4 cases §155
- path: evals/agent_runtime/expected/
  action: create
  reason: required/forbidden/unresolved por case §160
- path: evals/agent_runtime/reports/
  action: create
  reason: artefatos de resultado §74
- path: tests/test_agent_value_eval.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: configs = conjuntos de estagios habilitados; baseline A =
    spine deterministico; necessity deriva do vetor, nao de escalar
  rejected:
  - score unico (§57 proibe)
  - fingir custo sem provider (§55 proibe)
  rollback: remover modulo + fixtures + teste
covers:
- part: agent_value_eval
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — AGENT_VALUE_EVAL
