# Cycle 6 — Wave Evidence (convergence execution)

Evidencia nomeada por wave de `prompt_evo_cycle6.md` (§137-149). Status de
cada wave e medido contra artefato existente — nada aqui e auto-declaracao.
Legenda: PROVADO = artefato + gate/teste executado neste ciclo;
EXISTENTE = artefato ja provado em ciclo anterior e re-verificado;
PARCIAL = cobertura com lacuna nomeada.

| Wave | Escopo §137 | Status | Evidencia nomeada |
|---|---|---|---|
| W0 | baseline + audit | PROVADO | `docs/cycle6/CONVERGENCE_AUDIT.md`, `CROSS_VERTICAL_MATRIX.md` (0905187) |
| W1 | contract alignment | PROVADO | `azure/fingerprint.py`, `migration evidence_paths`, `evals/convergence/` 20/20 (3455e73) |
| W2 | real agent runtime | EXISTENTE | `evals/host_proof/claude_code.json` (claude -p via adapter, usage medido, trace sha256); `runtimes/` base+generic+playbook+host+registry+fallback; `docs/agentic/HOST_EXECUTION.md`; `runtime.status` vocab `declared→value_evaluated` em `runtimes/base.py:35` |
| W3 | agent A/B value | EXISTENTE | `evals/agent_runtime/reports/*.host.json` (4 verticais), `EMPIRICAL_AGENT_VALUE.md`, `tests/test_agentic_value*` |
| W4 | eval control plane | EXISTENTE | `evals/evolution.py`, `decision_replay.py`, `metric_compiler.py`, `lifecycle.py`, `policy.py`; gates `check_decision_*` |
| W5 | state/cache/recovery | EXISTENTE | `paths.py::state_dir` + `SPARKFORGE_AZURE_STATE_DIR` override; `tests/test_decision_kernel_state.py`, `test_runtime_convergence_checkpoint.py`, `test_cache_contracts.py`, `test_recovery_governance.py`; `collectors/recover.py` (taxonomia FailureKinds) |
| W6 | evidence/claims | EXISTENTE | `scripts/check_claims.py` (25/25 verdes ciclo 11), content-addressed receipts, `receipt/_hash.py`, `observability/context_ledger.py` |
| W7 | security red-team | EXISTENTE | `tests/test_redteam_security.py` — 32 testes: injecao, tool allowlist/denylist, output poisoning, quarentena, memoria por raiz, segredo por formato |
| W8 | large corpus + lab | PROVADO | corpus sintetico 25 modulos/5 dominios (slice isolation), contaminacao dominio/grafo/memoria/agente (949c67e) |
| W9 | supply chain | EXISTENTE | `scripts/verify_wheel.py` (wheel reproduzivel sha256 identico em 2 builds, ciclo 11), `scripts/check_supply_chain.py`, SBOM CycloneDX, lock check |
| W10 | freeze readiness | EXISTENTE | `docs/agentic/AGENTIC_ARCHITECTURE_FREEZE.md` (6/6 frozen); `docs/architecture/*FREEZE*` ciclo 11 — 8/8 §133 |
| W11 | closure | ESTE CICLO | `OUTCOME_BRIEF.md` (este documento + brief final) |

## Gaps medidos e fechados NESTE ciclo

1. `environment_fingerprint` ausente em databricks (3/4 verticais emitiam
   em `case_meta`) — fechado por `azure/fingerprint.py`.
2. `evidence_paths` ausente em migration — fechado por
   `migration._evidence_paths` (finding → facts → arquivo).
3. `evals/convergence/` nao existia — criado com 4 casos, 5 profiles,
   namespaces medidos, 20/20 celulas.
4. findings descritivos de stream (`SF-STR-LOSS-RISK` → area
   `SF-STR-LOSS`) nao casavam `findings_area: SF-STR` — o specialist de
   streaming ficava sem rota para os proprios findings. Corrigido com
   match de sub-area por fronteira de hifen em `case/router.py`.

## Gaps honestos que permanecem (nao bloqueantes, nomeados)

- `azure/memory.py` (`record_access_case`/`env_fingerprint`) nao tem
  consumidor real — vive em `doc-only` por decisao; a memoria efetiva e
  `agentic/memory.py` (decision records, env-scoped retrieval).
- Context Gateway / TokenSave / CodeIntel nao estao no hot path dos
  pipelines deterministicos — sao superficie de consumo LLM/MCP, por
  design (§10). Os pipelines nao leem repos nem chamam LLM.
- Pipelines nao exercitam `collectors/recover.py` — coleta live e outra
  superficie (`cmd_collect`), fail-closed por construcao offline.

## Invariantes §20 — estado medido

| Invariante | Como e verificado |
|---|---|
| sem finding verificado sem evidencia | runner: finding sem `evidence` ou citando `f_*` inexistente reprova |
| `unknown != healthy` | `unresolved` so em `allowed_unresolved` do caso |
| segredo nunca no relatorio | runner procura `BEGIN PRIVATE KEY`, `SharedAccessKey=`, `AccountKey=`, `client_secret`, `passwd=` na serializacao |
| DATA_ONLY nunca escalado | `trust.instruction_authority == "data_only"` nos 4 verticais, todo profile |
| evidencia cross-env nao misturada | fingerprint em `case_meta` + `retrieval.environment` gate |
| tokens desconhecidos != 0 | `usage.status` medido/unresolved (nao inventado) — host_proof |
