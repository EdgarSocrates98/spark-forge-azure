---
sdd: 1
feature: TOKENSAVE_PROOF
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/TOKENSAVE_PROOF/explore.md
  sha256: "c98e1fe6e3465c6470a6ae9bba40c7c0ae7b1ecb654b27297129b34a165a69c0"
hypothesis:
  claim: "O TokenSave reduz bytes lidos no caso real do vertical em comparação com leitura ingênua, e o ledger mede honestamente nível/bytes/hit sem inventar tokens"
  prediction: "benchmark reporta bytes_read < baseline para economy/balanced/deep, distribuição por nível, taxa de full-read baixa, e tokens observados ausentes → 'unresolved'"
  experiment: "pytest tests/test_tokensave_benchmark.py + artifacts do benchmark"
acceptance:
  - id: AC1
    statement: "benchmark roda o caso UC/ADLS em baseline/economy/balanced/deep e emite métricas comparáveis"
    verified_by: {kind: test, ref: tests/test_tokensave_benchmark.py::test_benchmark_profiles_vs_baseline}
  - id: AC2
    statement: "métricas incluem level distribution, full_read_rate, index_hit_rate, cache_hit_rate, context_reuse_rate, bytes_read e bytes_avoided; tokens só quando observados"
    verified_by: {kind: test, ref: tests/test_tokensave_benchmark.py::test_metrics_are_measured_not_invented}
  - id: AC3
    statement: "o ladder para no primeiro nível suficiente: L2 suficiente não dispara L3-L6"
    verified_by: {kind: test, ref: tests/test_tokensave_benchmark.py::test_stops_at_first_sufficient_level}
  - id: AC4
    statement: "read_full só no profile deep com reason declarada; nos demais é recusado"
    verified_by: {kind: test, ref: tests/test_tokensave_benchmark.py::test_full_read_is_rare_and_gated}
success:
  - id: SC1
    metric: "artefato de benchmark commitável prova bytes_avoided>0 no caso real e tokens declarados honestamente"
    source: "evals/token_efficient benchmark doc + pytest"
out_of_scope:
  - "router de modelo provider-side; claims de tokens sem observação real"
unknowns: []
change_kinds: [tool_or_verb]
---

# Define — TOKENSAVE_PROOF

Economia observável, não marketing: o benchmark mede bytes no caso real do
vertical; token provider permanece `unresolved` até existir observação.
