# Forge Lab — migração ADF/Synapse → Fabric (Cycle 5)

Corpus determinístico em `tests/fixtures/migration/` — 22 cenários do
prompt (§252-273). Cada caso é um bundle `case.yaml` + `estate.json`
(+ `assessment.json`/`validation.json`/`notebooks/` quando o cenário pede)
com oráculo `expect:` verificado por `run_migration_suite`:

```bash
sparkforge-azure migration assess --suite tests/fixtures/migration
```

`expect` suporta `status`, `plan_status`, `readiness.<asset>`,
`verdict` (validação), `strategy` (recomendação de dados),
`sharing_finding`, `upstream_blocker`.

| Caso | Cobre | Esperado |
|---|---|---|
| m01-ready | pipeline só com atividades suportadas | `status=pass`, READY |
| m02-ssis-blocked | ExecuteSSISPackage | `blocked`, dimensão `unsupported` |
| m03-global-params | global parameters | variable_library candidate, `review` |
| m04-shir | IR self-hosted | `review`, manual_refactor |
| m05-legacy-auth | windows_auth | `review`, auth manual_refactor |
| m06-synapse-custom | Custom activity em pipeline Synapse | `blocked` |
| m07-mssparkutils-ls | getSecretWithLS | `review`, refactor finding |
| m08-catalog-api | spark.catalog.listFunctions | `blocked` |
| m09-spark-config | spark.synapse.* + shuffle.partitions | `review` (mixed) |
| m10-library-unknown | whl sem compat provada | `unresolved`, nunca unsupported |
| m11-delta-shortcut | ADLS delta vivo | `strategy=shortcut` (candidato) |
| m12-retirement-copy | retirement declarado | `strategy=copy` |
| m13-shared-ls | 2 pipelines, LS windows_auth | `do_not_consolidate` |
| m14-dep-cycle | ciclo depends_on pipeline→pipeline | `plan_status=REVIEW` |
| m15-upstream-blocked | upstream SSIS blocked | `blocked` + upstream_blocker |
| m16-rowcount-dq | row count =, dq ≠ | validação `fail` |
| m17-perf-regression | funcional =, duração 4× | validação `fail` |
| m18-wrong-identity | principal diverge | validação `fail` |
| m19-stale-assessment | assessment de 2020 | `review` + stale flag |
| m20-official-conflict | oficial "not compatible" vs Forge READY | `review` + conflito |
| m21-malicious-metadata | prompt injection em descrições | `pass`, taint DATA_ONLY |
| m22-insufficient | tipo de atividade desconhecido, sem target | `unresolved` |

## Verdades do lab

- Identidade é ARM id/GUID; display name é atributo.
- Ausência de assessment é `unresolved`, nunca READY implícito.
- Shortcut é recomendação com evidência, nunca mandato.
- Ciclo de dependência é REVIEW — o planner nunca inventa ordem.
- Validação é por dimensão; passar em row_count não absolve schema.
