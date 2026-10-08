# Fabric lab — OneLake/Shortcuts/Spark/Capacity (prompt_evo_cycle3)

Labs do vertical Microsoft Fabric. Tudo offline, determinístico,
reproduzível — a mesma disciplina do access lab.

## Scenarios f01–f16 — `diagnose fabric --suite`

```bash
sparkforge-azure diagnose fabric --suite tests/fixtures/fabric
sparkforge-azure diagnose fabric --suite tests/fixtures/fabric --profile deep
```

Cada diretório `tests/fixtures/fabric/fNN_*` é um case bundle
(`case.yaml` + artefatos JSON: `workspace`, `capacity`, `items`,
`lakehouse`, `shortcuts`, `connections`, `identity`, `environment`,
`pipelines`, `onelake_security`). O bloco `expect:` do `case.yaml` é o
oráculo.

| #   | fixture                          | esperado                                     |
|-----|----------------------------------|----------------------------------------------|
| f01 | item_permission_denied           | `denied` / `fabric_workspace` (sem role)     |
| f02 | onelake_denied                   | `denied` / `onelake_security`                |
| f03 | passthrough_source_denied        | `denied` / `source_access` (caller sem grant)|
| f04 | delegated_ok                     | `pass` (delegated via connection testada)    |
| f05 | shortcut_target_missing          | `unresolved` (target ausente ≠ denied)       |
| f06 | sjd_missing_lakehouse            | `denied` / `spark_job`                       |
| f07 | sjd_wrong_lakehouse              | `denied` / `spark_job`                       |
| f08 | runtime_mismatch                 | `denied` / `spark_runtime`                   |
| f09 | overload_not_throttled           | `pass` — overload ≠ throttle                 |
| f10 | capacity_throttled               | `denied` / `capacity` (evidência explícita)  |
| f11 | slow_spark_healthy_capacity      | `findings` / `spark_perf` (SF-PY)            |
| f12 | pipeline_wrong_workspace         | `denied` / `data_factory`                    |
| f13 | tenant_mismatch                  | `denied` / `cross_environment`               |
| f14 | malicious_metadata               | trust `suspicious`, veredito inalterado      |
| f15 | insufficient                     | `unresolved` (ABSTAIN honesto)               |
| f16 | viewer_write_denied              | `denied` / `item_permission`                 |

Medido: a suite fecha com **16 passed / 0 failed**. Cobertura:
`tests/test_fabric_*.py` (13 arquivos), `tests/test_architecture_layers.py`.

## O que o lab prova

- **Unknown ≠ denied**: f05/f15 nunca produzem ALLOW nem DENY inventado;
  camada fica `unresolved` com o artefato que faltaria coletar.
- **Confused deputy**: caller principal e effective identity delegada são
  preservados separadamente (f03 passthrough vs f04 delegated).
- **Overload ≠ throttling**: f09 (utilização alta, sem evidência de
  throttle) não reporta capacity; f10 exige `CapacityLimitExceeded`/429.
- **Cross-environment**: f12/f13 comparam tenant/workspace escopos
  (`environment.scope` facts → `SF-FAB-013`).
- **Trust**: f14 injeta prompt-injection em `displayName` de item —
  `trust.taint == "suspicious"`, dados nunca sobem autoridade.

## Live collection (opt-in, read-only)

`collectors/fabric.py` reusa a boundary compartilhada
(`collectors.base`): `from_export(artifact)` ingere JSON exportado;
`collect_live(workspace_id, fetch=…)` exige `fetch` injetado (sem SDK
empacotado) e só emite GETs `api.fabric.microsoft.com/v1`; falhas viram
`unresolved` com `failure_class` — nunca erro silencioso.
