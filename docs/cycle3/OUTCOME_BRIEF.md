# Cycle 3 — Outcome Brief (Microsoft Fabric deep vertical)

`prompt_evo_cycle3.md` implementado em fases/ondas com commit por wave
na branch `feat/cycle3-fabric-deep` (base: `068b922` — merge do closure
do Cycle 2).

## SHAs

| Marco | SHA |
|---|---|
| `BASE` | `068b9221f63a75ec765c69b694ee8e7ae6bb7b08` (main pós-Cycle-2) |
| `WAVE0_SDD` | `e17c27b` — 5 sub-SDDs abertos (gate vermelho honesto: `test_not_written`) |
| `VERTICAL` | `9f87599` — model+casefile+extract+diagnose+pipeline+graph+rules+lab 16 |
| `SURFACES` | `1ed05cd` — `diagnose fabric`, `sfa_diagnose_fabric`, packs, corpus TokenSave |
| `COLLECTORS` | `4c64bd6` — collector export/live-injetado, doctor `fabric_vertical`, fingerprint, waste |
| `SDD_GREEN` | `a2e9cf5` — build_reports red→green reais; gate 11/11 features ok |

## O que existe (medido)

- **Domínio**: `fabric/model.py`, `casefile.py` (11 artefatos),
  `extract.py` (~20 kinds `fabric.*`/`onelake.*`/`environment.scope`),
  `diagnose.py` (cadeia: env→workspace→item→onelake→shortcut→
  source→lakehouse→runtime→sjd→capacity→data_factory).
- **Regras**: `rules/catalog/fabric.yaml` (`SF-FAB-*`) + reuso do catálogo
  `SF-PY-*` no scanner PySpark compartilhado.
- **Lab**: `tests/fixtures/fabric/f01..f16` — **16 passed / 0 failed**
  (`diagnose fabric --suite`).
- **Grafo**: layer `fabric` no registry Graphfy — 17 kinds SaaS
  (tenant→capacity→workspace→item→lakehouse→shortcut→connection→
  external_target…), federation por Fabric id (não ARM).
- **Surfaces**: CLI `diagnose fabric --bundle|--suite [--profile]`,
  MCP `sfa_diagnose_fabric` (read_only), collector
  `from_export`/`collect_live` (fetch injetado, só GETs), doctor
  `fabric_vertical`.
- **Knowledge**: 6 packs Fabric escopados por `failure_layer`;
  `excluded_domains` prova isolamento entre verticais.
- **Economia**: `fabric/fingerprint.py` (memória ancorada a
  tenant/capacity/workspace), `fabric/waste.py` (hipóteses de waste sobre
  spans), corpus `evals/token_efficient/fabric_case` no benchmark.

## Invariantes provados no lab

- Unknown nunca vira ALLOW; artefato ausente → `unresolved` com
  `artifact`/`artifact_present` (f05, f15).
- Caller ≠ effective identity delegada (f03 vs f04) — confused deputy
  não colapsa.
- Overload ≠ throttling (f09 vs f10) — throttle exige evidência explícita.
- Cross-tenant/workspace → `SF-FAB-013` + `cross_environment` (f12, f13).
- Taint em `displayName`/metadados → `trust.suspicious`, veredito
  inalterado (f14).
- Workspace Fabric nunca recebe ARM id fabricado (SaaS plane).

## Gates

```
sdd.checks      ok=True — 11 features, 0 refused, 0 unresolved
fabric suite    16 passed / 0 failed
pytest foco     55 fabric tests verdes (13 arquivos)
ruff            clean
REMOTE_CI       NOT_OBSERVED (quota GitHub — ignorado conforme instruído)
```
