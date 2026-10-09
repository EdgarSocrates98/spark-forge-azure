---
sdd: 1
feature: TOKEN_EFFICIENT_BENCHMARK
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/TOKEN_EFFICIENT_BENCHMARK/design.md
  sha256: 8438581f1340182462b1ced621af8057c9647a3e76b5011f37c19b32bd255480
tasks:
- id: T1
  files: [tests/test_token_benchmark.py]
  covers: [AC1, AC2, AC3, AC4, AC5]
  test:
    path: tests/test_token_benchmark.py
    name: test_every_cell_matches_its_gabarito
- id: T2
  files:
  - evals/token_efficient/suite.yaml
  - evals/token_efficient/fixtures/benchmark_cases.yaml
  - sparkforge_azure/evals/token_benchmark.py
  covers: [AC1, AC2, AC3]
  test:
    path: tests/test_token_benchmark.py
    name: test_suite_loads_with_sha_and_replay_contract
- id: T3
  files:
  - scripts/check_token_efficient_bench.py
  - evals/parity/token_benchmark_baseline.json
  covers: [AC2, AC4]
  test:
    path: tests/test_token_benchmark.py
    name: test_tokens_are_unresolved_not_zero_without_provider
---

# Plan — TOKEN_EFFICIENT_BENCHMARK

T1 contrato; T2 suite+gabarito+loader (a matriz ja sai verde porque o
gabarito foi derivado executando o planner real, nao transcrito); T3 gate
offline + baseline gravado.
