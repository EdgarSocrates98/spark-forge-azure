---
sdd: 1
feature: TOKEN_EFFICIENT_BENCHMARK
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/TOKEN_EFFICIENT_BENCHMARK/define.md
  sha256: 051cc074af97ee914b2d84edf05f032d67069b6191a43712aaf2f61a578bd244
files:
- path: sparkforge_azure/evals/token_benchmark.py
  action: create
  reason: load/run/compare da matriz — porte do AWS com as duas diferencas
    reais (catalogo mcp.tools + chave benchmark_fixture)
- path: evals/token_efficient/fixtures/benchmark_cases.yaml
  action: create
  reason: gabarito por case id com expected_* e expected_execution_plan por
    profile derivado do planner real
- path: evals/token_efficient/suite.yaml
  action: modify
  reason: declara benchmark_fixture + metadados da matriz (baseline_id,
    profiles, quality_axes, fixtures adicionais)
- path: scripts/check_token_efficient_bench.py
  action: create
  reason: gate offline — valida registro e executa a matriz conferindo cada
    celula contra o gabarito
- path: evals/parity/token_benchmark_baseline.json
  action: create
  reason: baseline medido gravado — artifact, nao source of truth
- path: tests/test_token_benchmark.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: gabarito dedicado benchmark_cases.yaml com `id` por caso;
    quality_cases.yaml (case_id q-*) continua servindo o avaliador de rota
    que ja o consome
  rejected:
  - reusar quality_cases.yaml como gabarito (ids q-* divergem dos ids de
    dominio da suite; dois contratos num arquivo)
  - normalizar case_id->id no loader (adota silenciosamente divergencia de
    schema em vez de declarar qual fixture serve qual papel)
  rollback: apagar benchmark_cases.yaml; o loader falha com ids divergentes
- id: D2
  choice: expected_execution_plan derivado do planner real antes de gravar o
    gabarito — cada expected_* foi conferido executando a matriz
  rejected:
  - transcrever expected do AWS (planner Azure tem triggers e perfis iguais,
    mas o gabarito tem que ser medido aqui, nao copiado)
  rollback: re-derivar planos e regravar o gabarito
- id: D3
  choice: compare recusa com razao nomeada (suite_mismatch,
    quality_axes_mismatch, matrix_cells_mismatch) em vez de diff parcial
  rejected:
  - diff best-effort sobre celulas divergentes (parece comparacao, e
    comparacao falsa)
  rollback: voltar ao diff parcial — nao recomendado
covers:
- part: token_benchmark
  acceptance: [AC1, AC2, AC3, AC4, AC5]
---

# Design — TOKEN_EFFICIENT_BENCHMARK

## Fluxo

```
suite.yaml --+--> load_benchmark_suite --> validate ids + sha + floors
fixtures/ ---+        |
                      v
            run_benchmark_matrix: EvaluationRunner.run_context_benchmark
            nos 3 profiles sobre os MESMOS 15 cases
                      |
                      v
        45 celulas: status/evidence/unresolved/plan conferidos
        + payload_bytes + tokens_unresolved (sem provider)
                      |
                      v
        compare_benchmark_matrix: diff por celula ou recusa nomeada
```

## Pontos de honestidade preservados do AWS

- `provider_tokens=None` + `tokens_unresolved=True` quando nao ha host
  transcript — nunca 0.
- `_axis_value` extrai `execution_plan.kind` e `unresolved` como eixos de
  primeira classe — o plano do planner e medido, nao assumido.
- `_summary` usa `median_low`/`max` (deterministico, sem media movel de
  floats).
- `compare` nunca inventa score: devolve before/after/delta por celula.

## Diferenca real Azure

`ContextGateway(full_catalog())` — o catalogo vem das tools `sfa_*` do MCP,
nao da tabela `adapters.tools` do AWS. E o gabarito mora em
`benchmark_fixture` porque `quality_fixture` aqui ja e outro contrato.
