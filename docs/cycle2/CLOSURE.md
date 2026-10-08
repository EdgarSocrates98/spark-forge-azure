# Cycle 2 — closure record

```text
CYCLE_2          = CLOSED
DATE             = 2026-10-08
BASE_SHA         = b1caf70280a95479f4dcd9bb98b119b46ce823e5
FINAL_CODE_SHA   = 84a7761
EVIDENCE_SHA     = 38860e8
MERGE            = 3b280dd  (PR #4 → main — base de fechamento)
CLOSURE_BRANCH   = chore/cycle2-closure  (este commit de documentação/audit-fix)
                 O merge desta PR em `main` produz um novo SHA — o registro
                 autoritativo é o merge commit do PR, não este documento.
LOCAL_GATES      = PASS    (pytest 2541/9sk, ruff, surface, claims, knowledge, skills, sdd)
REMOTE_CI        = NOT_OBSERVED (quota indisponível — não declarado green)
```

## Aceite — resumo

| Área | Resultado medido |
|---|---|
| Suite | 2541 passed, 9 skipped, 0 failed |
| Access suite | 10/10 cenários determinísticos |
| MCP | runtime real; matrix 16 covered / 5 delegated_to_sdk / 2 not_applicable |
| Graphfy | hot path — evidence_paths derivados do grafo |
| TokenSave | 9920 B baseline → 1964–2981 B; tokens `unresolved` (offline) |
| Trust/Security | redação na fronteira; `cross_environment` é finding |
| Doctor | 17 checks ok, `network_calls: 0`, `cloud_mutation: none` |
| Claims | 10 claims stamped; `suite-green` rejeita `N failed,` prefix |
| SDD | 6 features, `refused: []`, `unresolved: []` — gate real: `sparkforge_azure.sdd.checks.check` via suite (`test_fixtures_golden_sdd`, `test_sdd_eval_suite`); o verbo `sdd` no CLI é tool_ref planejado (ROADMAP) |

## Fix encontrado no closure

`agentops inspect|timeline|critical-path` lia `cwd/.sparkforge-azure/traces.db`
ignorando `SPARKFORGE_AZURE_STATE_DIR` — assimetria write/read. Corrigido com
`paths.state_dir()` unificado em store/doctor/decision-cache/agentops CLI.

## Deferred

| Item | Status | Blocker? |
|---|---|---|
| Live Azure collector proof | DEFERRED_EXTERNAL | não |
| Provider token observation | DEFERRED_EXTERNAL | não |
| Persistent live cache | BACKLOG | não |
| Recorded Tier-3 transcripts | BACKLOG | não |
| Fabric deep vertical | NEXT CYCLE | não |

## Gate do próximo cycle

Cycle 3 (candidato: Fabric deep vertical) só inicia quando
outcome/claims/surface/tests/docs deste closure estiverem verdes em `main`.
