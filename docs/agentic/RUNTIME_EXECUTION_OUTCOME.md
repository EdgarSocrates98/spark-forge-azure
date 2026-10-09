# Runtime Execution Outcome — cycle 9 (§190-191)

| Campo | Valor |
|---|---|
| BASE_SHA | `95b1aa5` |
| FINAL_SHA | (preenchido no merge) |
| RUNTIMES_DECLARED | 6 (claude_code, devin_cli, devin_desktop, copilot_ci, codex, generic) |
| RUNTIMES_ADAPTER_IMPLEMENTED | 6/6 — boundary real em `agentic/runtimes/` |
| RUNTIMES_HOST_PROVEN | **0/6** — sem transcript de host nesta wave (§9) |
| AGENTS_CONTRACT_READY | 40/40 |
| AGENTS_HOST_EXECUTED | 0 — roles deterministicas executam INLINE de verdade (extractor, inventory, judge, verifier, synthesizer); probabilisticas voltam `unresolved` nomeado |
| AGENTS_VALUE_PROVEN | UNRESOLVED — valor empirico exige host; harness mede e reporta isso |
| DATBRICKS_EVAL / FABRIC_EVAL / STREAMING_EVAL / MIGRATION_EVAL | reports em `evals/agent_runtime/reports/` — frontier A-D, necessity UNRESOLVED/NEUTRAL (sem ganho de info sem host) |
| SPECIALIST/VERIFIER/REVIEWER/CRITIC/REFEREE/TEST_ENGINEER/EVALUATION_SPECIALIST VALUE | verifier: falsificacao deterministica real (finding sem evidence -> refuted); demais: UNRESOLVED sem host |
| QUALITY_FRONTIER | estabelecida por caso (A-D) |
| SECURITY | 8 cenarios §112-120 verdes — DATA_ONLY mantido, escalacoes negadas |
| BUDGET | budgets por estagio no receipt; tokens unresolved (§55) |
| CONTEXT | RoleContextPlan por estagio; acumulado sem transcript cru (§27/38) |
| AGENTOPS | AgentSpan com runtime/mode/spawn_id/output_valid/tool_calls (§122) |
| CLAIMS | atualizadas no lock |
| SURFACE | 17 tools MCP, drift [] |
| TESTS | ver suite-green no lock |
| FREEZE_STATUS | **candidate** — bloqueios: `host_proof_missing`, `value_eval_unresolved_without_host` |

## Resposta a §240

Para cada classe de agente, "melhora outcomes suficiente para o custo?":
nao medido sem host — e o sistema **reporta** isso em vez de afirmar.
O que esta provado: deterministic spine executa, degrada com razao
nomeada, handoffs re-filtram, seguranca segura, e a fronteira A-D existe
para quando um host real for ligado (§231: um host primeiro).
