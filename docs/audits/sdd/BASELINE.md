# SDD Baseline — spark-forge-azure (Onda 0)

- SHA `13cfff6dbd13` · branch `release/cycle-2.7-patch-version` · `.git` present · ~135 dirty files (pré-existentes)
- Python ≥3.10 · suíte `test_sdd_cli|test_sdd_eval_suite|test_sdd_migration|test_fixtures_golden_sdd`
- SDD: `sparkforge_azure/sdd/` portado do AWS (COPY_SAFE) — checks(869ln)/load/stamp/status/schema/change_kinds — **motor funciona**
- CLI `sparkforge-azure sdd {check|status}` apenas — `stamp` existe como módulo mas **não é verbo**
- Skills canônicas `skills/` (24 dirs) — **zero `sdd-*`**; mirrors via `scripts/sync_skill_mirrors.py`

## Findings

| # | Sev | Finding | Evidência |
|---|---|---|---|
| F1 | P0 | `stamp` inalcançável via CLI + `--repo`/`--root` ausentes → operator flow impossível via CLI | cmd_sdd.py:20-26 |
| F2 | P0 | **Todas as 6 skills sdd-* ausentes** enquanto docs mandam `sdd-define` | skills/ vs docs/sdd/README.md:24 |
| F3 | P0 | `docs/sdd/templates/` ausente — agentes escrevem frontmatter do zero | — |
| F4 | P0 | `docs/gates-por-mudanca.md` ausente — change_kinds.yaml aponta pra doc inexistente | checks.py:621 |
| F5 | P0 | Strings dizem `sparkforge sdd …` (binário AWS) dentro do pacote Azure | checks.py:159,173,279 |
| F6 | P1 | Test files ausentes vs AWS: test_sdd.py (drift lock), ac_vermelho, operator, skills | — |
| F7 | P1 | README.md reduzido (sem phase loop, operator path, skills table, CONTRATO.md) | docs/sdd/README.md |
| F8 | P1 | 66 features, ~65 plan.md, **0 ship.md** — ship gates nunca exercitados | docs/sdd/ |
| F9 | P1 | Skill structure mais rasa que AWS (sem references/, scripts/, _shared/) | skills/ |
| F10 | P2 | parity.yaml/manifest.json marcam sdd "ported/SUPPORTED" — enganoso | parity.yaml:502 |
| F11 | P2 | `scripts/_gen_sdd_fixtures.py` "rode uma vez e apague" ainda shipped | — |

## Capacidades preservadas

Motor SDD completo portado (schema cascade, refusal taxonomy, gate tables, stamp atômico), eval suite sdd, fixtures golden, grill-gate doc (4 perguntas).
