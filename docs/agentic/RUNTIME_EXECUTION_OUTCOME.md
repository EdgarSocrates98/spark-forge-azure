# Runtime Execution Outcome — cycle 9+10 (§190-191)

| Campo | Valor |
|---|---|
| BASE_SHA | `95b1aa5` |
| FINAL_SHA | `40d4067` (cycle 9 merge) + cycle 10 `feat/cycle10-host-proof` |
| RUNTIMES_DECLARED | 6 (claude_code, devin_cli, devin_desktop, copilot_ci, codex, generic) |
| RUNTIMES_ADAPTER_IMPLEMENTED | 6/6 — boundary real em `agentic/runtimes/` |
| RUNTIMES_HOST_PROVEN | **1/6** — `claude_code` com transcript real em `evals/host_proof/claude_code.json` (ping, `status=completed`, `trace_ref sha256:1d1c…`, custo medido $0.66) |
| AGENTS_CONTRACT_READY | 40/40 |
| AGENTS_HOST_EXECUTED | 4 specialists executados de verdade via `claude -p`: azure-databricks, onelake, fabric, event-hubs — `subagent`, status `completed`, 0 violacoes de schema |
| AGENTS_VALUE_PROVEN | 4/4 specialists avaliados em host: necessity **USEFUL** (evidence_gain>0 vs baseline A) — reports `evals/agent_runtime/reports/<case>.host.json` |
| DATBRICKS_EVAL / FABRIC_EVAL / STREAMING_EVAL / MIGRATION_EVAL | frontier A-D + host report por case; custo real medido: **$2.79 total** (~$0.70/spawn, quase todo cache-creation do CLI) |
| SPECIALIST VALUE | USEFUL ×4 — ganho real de evidencia/hipoteses; finding proibido = 0 |
| VERIFIER VALUE | falsificacao deterministica real (finding sem evidence → refuted), executa INLINE sem custo |
| REVIEWER/CRITIC/REFEREE/TEST_ENGINEER/EVALUATION_SPECIALIST | UNRESOLVED em host (nao exercitados na config B) — declarado, nao simulado |
| QUALITY_FRONTIER | estabelecida por caso (A-D) + ponto medido em host |
| SECURITY | 8 cenarios §112-120 verdes — DATA_ONLY mantido, escalacoes negadas |
| BUDGET | budgets por estagio; tokens/custo **measured** nos reports host |
| CONTEXT | RoleContextPlan por estagio; prompt host = task + unresolved + schema (§28) |
| AGENTOPS | AgentSpan com runtime/mode/spawn_id/output_valid/tool_calls (§122) |
| CLAIMS | atualizadas no lock |
| SURFACE | 17 tools MCP, drift [] |
| TESTS | ver suite-green no lock |
| FREEZE_STATUS | **frozen** — 6/6 condicoes `met` com evidencia nomeada (`evaluate_freeze()`) |

## Resposta a §240

Para cada classe de agente, "melhora outcomes suficiente para o custo?":
specialist em host = **USEFUL** medido — produziu evidencia/hipoteses
novas por ~$0.70/spawn. O custo real do `claude -p` e dominado por
cache-creation (~101k tokens por chamada): otimizacao obvia e reuse de
sessao ou modelo menor para pings — registrado como follow-up. Verifier
segue deterministico e gratis. Reviewers/referee nao exercitados em host
— valor segue UNRESOLVED, nao assumido.
