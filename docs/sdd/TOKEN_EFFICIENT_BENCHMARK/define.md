---
sdd: 1
feature: TOKEN_EFFICIENT_BENCHMARK
phase: define
profile: dev
status: done
hypothesis:
  claim: 'a matriz de benchmark token-efficient do irmao AWS existe no Azure
    com o mesmo contrato: casos identicos nos tres profiles (economy,
    balanced, deep), eixos crus sem score composto, tokens_unresolved
    declarado sem provider, compare que recusa mismatch em vez de adivinhar'
  prediction: 'load_benchmark_suite valida suite+gabarito com sha256 e
    replay contract (>=50 tasks rotuladas), run_benchmark_matrix executa
    15 casos x 3 profiles = 45 celulas conferidas contra expected_*,
    compare_benchmark_matrix devolve diff por celula ou recusa nomeada'
  experiment: pytest tests/test_token_benchmark.py +
    scripts/check_token_efficient_bench.py
acceptance:
- id: AC1
  statement: 'load_benchmark_suite valida schema_version=1, ids de case
    suite<->gabarito identicos, sha256 sobre suite+fixtures, e fixture
    decision_control_plane com >=50 tasks rotuladas ou falha nomeada'
  verified_by:
    kind: test
    ref: tests/test_token_benchmark.py::test_suite_loads_with_sha_and_replay_contract
- id: AC2
  statement: 'run_benchmark_matrix cobre 15 casos x 3 profiles = 45 celulas
    e cada celula confere status/evidence/unresolved/execution_plan contra o
    gabarito benchmark_cases.yaml'
  verified_by:
    kind: test
    ref: tests/test_token_benchmark.py::test_every_cell_matches_its_gabarito
- id: AC3
  statement: 'profiles diferem apenas onde o planner permite escalacao:
    deep emite debate/reviewer/specialist, economy e balanced nunca'
  verified_by:
    kind: test
    ref: tests/test_token_benchmark.py::test_profiles_differ_only_where_escalation_is_allowed
- id: AC4
  statement: 'sem provider, provider_tokens=None e tokens_unresolved=True em
    toda celula — nunca zero fingido'
  verified_by:
    kind: test
    ref: tests/test_token_benchmark.py::test_tokens_are_unresolved_not_zero_without_provider
- id: AC5
  statement: 'compare_benchmark_matrix devolve diff por celula para matrizes
    da mesma suite e recusa suite/axes/cells mismatch com razao nomeada'
  verified_by:
    kind: test
    ref: tests/test_token_benchmark.py::test_compare_refuses_on_mismatch
success:
- id: SC1
  metric: 'scripts/check_token_efficient_bench.py sai 0 com 45/45 celulas ok
    e tokens_unresolved=45 declarado; evals/parity/token_benchmark_baseline.json
    gravado como baseline medido'
  source: python scripts/check_token_efficient_bench.py + pytest tests/test_token_benchmark.py
out_of_scope:
- 'score composto de qualidade (o contrato recusa compor eixos crus)'
- 'medicao de tokens de provider (exige host transcript — segue unresolved)'
- 'gabarito conceitual do bench (casos conferem expected_*, nao semantica livre)'
unknowns: []
change_kinds:
- fixture_corpus
---

# Define — TOKEN_EFFICIENT_BENCHMARK

Porte do `evals/token_benchmark.py` do irmao AWS (commit ab7f02e). A
diferenca real, nao renomeada:

- o catalogo do gateway Azure e `mcp.tools.full_catalog()` (tools `sfa_*`);
- a suite aceita `id` ou `suite_id` e o gabarito da matriz vive em
  `benchmark_fixture` — `quality_fixture` no Azure ja e ocupado pelo
  fixture de rota de qualidade que outro avaliador consome
  (`test_offline_federated_fixtures.py`);
- `decision_fixture` resolve `decision_plane_cases.yaml` declarado na
  suite; control-plane/calibration/host-replay sao validados do mesmo
  jeito (dentro do diretorio, schema_version=1, piso de tasks rotuladas).

O que NAO muda (contrato preservado): casos identicos nos tres profiles,
eixos crus (status, evidence_recall, false_positive_rate, unresolved,
execution_plan), nenhum score composto, `tokens_unresolved` explicito sem
provider, e `compare` que recusa em mismatch em vez de produzir diff
espurio.

## Casos (15, dominios Azure)

Adaptados do AWS para os dominios deste repo: Unity Catalog sobre ADLS,
cluster Databricks, skew Spark, grafo de dependencias de workspace
Fabric, qualidade Delta, Entra cross-tenant, review de write em
producao Fabric, migracao ADF->Fabric, otimizacao de join PySpark,
disponibilidade de tabela UC, manutencao Delta. `expected_execution_plan`
por profile foi derivado do `context/planner.py` real — deterministic
quando resolvido sem triggers, escalacao so no deep.

## Por que `benchmark_fixture` e nao reusar `quality_cases.yaml`

`quality_cases.yaml` usa `case_id` com ids `q-*` e alimenta outro
avaliador. Copiar `id` para dentro dele quebraria o consumidor atual e
misturaria dois contratos. Gabarito novo = contrato do benchmark,
sem efeito colateral.
