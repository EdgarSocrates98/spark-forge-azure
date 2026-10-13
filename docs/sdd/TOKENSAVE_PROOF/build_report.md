---
sdd: 1
feature: TOKENSAVE_PROOF
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/TOKENSAVE_PROOF/plan.md
  sha256: "f8d01c5d7ea5181944caeba937efc98595ce7285938e88b3a5f4ef62e2fa3df4"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-red-p0d && ../.venv/Scripts/python -m pytest tests/test_tokensave_benchmark.py::test_benchmark_profiles_vs_baseline tests/test_tokensave_benchmark.py::test_metrics_are_measured_not_invented -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_tokensave_benchmark.py::test_benchmark_profiles_vs_baseline tests/test_tokensave_benchmark.py::test_metrics_are_measured_not_invented -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-red-p0d && ../.venv/Scripts/python -m pytest tests/test_tokensave_benchmark.py::test_stops_at_first_sufficient_level tests/test_tokensave_benchmark.py::test_full_read_is_rare_and_gated -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_tokensave_benchmark.py::test_stops_at_first_sufficient_level tests/test_tokensave_benchmark.py::test_full_read_is_rare_and_gated tests/test_tokensave_benchmark.py::test_ladder_climbs_only_when_terms_missing -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd .tmp-red-p0d && ../.venv/Scripts/python -m pytest tests/test_tokensave_benchmark.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_tokensave_benchmark.py -q", exit: 0}
claims:
  - text: "benchmark roda o caso UC/ADLS em baseline + economy/balanced/deep com metricas comparaveis medidas do ledger"
    evidence_ref: "tests/test_tokensave_benchmark.py::test_benchmark_profiles_vs_baseline"
  - text: "metricas reportam bytes (level_distribution, full_read_rate, cache_hit_rate, context_reuse_rate, index_hit_rate, bytes_avoided); tokens ficam 'unresolved' sem observacao de provider"
    evidence_ref: "tests/test_tokensave_benchmark.py::test_metrics_are_measured_not_invented"
  - text: "o ladder para no primeiro nivel suficiente; L6 nunca dispara sozinho"
    evidence_ref: "tests/test_tokensave_benchmark.py::test_stops_at_first_sufficient_level"
  - text: "read_full e recusado fora do profile deep e exige reason declarada"
    evidence_ref: "tests/test_tokensave_benchmark.py::test_full_read_is_rare_and_gated"
change_id: "feat/cycle2-evolution"
---

# Build Report — TOKENSAVE_PROOF

Reds registrados num worktree da base (`b1caf70`): `test_tokensave_benchmark.py`
falha na coleta (exit 2 — `tokensave.benchmark` nao existia).

- `tokensave/benchmark.py`: corpus do caso real
  (`evals/token_efficient/access_case` = bundle s01 enriquecido, ~10KB, 11
  arquivos). Baseline = soma dos bytes do corpus (leitura ingenua). Cada
  profile roda `TokenSave.context()` com os mesmos termos exigidos; o ledger
  mede bytes por nivel, cache/reuse/full-read.
- Resultado medido: baseline 10415 bytes; economy 1964 (81% avoided),
  balanced/deep 2981 (71% avoided). Todos `sufficient` parando em L1 — a
  prova de que a escada para cedo no caso real.
- `tokens: "unresolved"` literal: sem provider, nao ha numero.
- `sparkforge-azure tokensave benchmark --case <dir> [--task] [--term]`
  imprime o report JSON. Nenhuma mudanca de engine foi necessaria — o ladder
  e o gate L6 ja estavam corretos; a onda provou com teste.
