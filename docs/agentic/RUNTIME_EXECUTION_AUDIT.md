# Runtime Execution Audit — cycle 9 baseline

§3–§5 de `prompt_evo_agent_runtime.md`. Auditoria do que a superfície de
execução **realmente é** antes desta wave — a distinção que importa:
planejamento/gating ≠ execução de agente.

- BASE_SHA / CURRENT_MAIN_SHA: `95b1aa5`
- Fleet fingerprint: 40 agents, todos `ready`, autonomy ≤ L2
- Ambiente: sem host LLM ao alcance local — toda classificação abaixo
  assume isso (§9: sem prova → `DECLARED_UNPROVEN`, nunca `HOST_PROVEN`).

## 1. Camadas auditadas

| Módulo | O que é | Execução real? |
|---|---|---|
| `agentic/runtime.py` | `RuntimeName`, `RuntimeCapabilities`, `AgentRuntime` Protocol, `execution_strategy` | Não — contrato + tabela de capacidades **declaradas** (bound a `parity.yaml` só em 2 campos) |
| `agentic/spawn.py` | `decide_spawn` / `decide_team` | Não — **spawn gate** (planejamento): decide SE/QUEM, nunca executa |
| `agentic/pipeline.py` | `plan_pipeline` | Não — ordem de estágios planejada (§30) |
| `agentic/handoff.py` | `admit_handoff` | Não — admissão/policy de handoff, não transporte entre execuções |
| `agentic/executor/run.py` | executor de regras/juízo/arbitragem | Sim — **deterministic core** (puro, offline) |
| `agentic/checkpoint.py` | `SemanticCheckpoint` | Sim — mas não carrega estado de execução de agents (§46 gap) |
| `agentic/spans.py` | spans AgentOps | Sim — emissão de telemetria, sem campos de runtime (§122 gap) |
| `agentic/blackboard.py` | append/propose/version/supersede | Sim — storage, não transporte host |
| `agentic/routing.py` | `explain_route` / `ROUTING_TABLE` | Sim — roteamento determinístico |

**Resumo honesto:** toda a camada agentic é *planning + gating +
contratos*. O que falta é o adapter boundary real (§11–§22) e a engine
que liga `plan_pipeline → spawn gate → adapter → resultado estruturado`.

## 2. Runtimes — status model §7

```
DECLARED → ADAPTER_IMPLEMENTED → INTEGRATION_TESTED → HOST_PROVEN → EVALUATED
                                                         ↘ DEGRADED / UNAVAILABLE
```

| Runtime | Capabilities (parity.yaml) | Adapter | Status inicial | Prova |
|---|---|---|---|---|
| `claude_code` | subagent + mcp declarados | — | `DECLARED_UNPROVEN` | nenhuma — sem transcript/teste de host |
| `devin_cli` | subagent + mcp declarados | — | `DECLARED_UNPROVEN` | nenhuma |
| `devin_desktop` | subagent + mcp declarados | — | `DECLARED_UNPROVEN` | nenhuma |
| `copilot_ci` | `playbook` apenas | — | `DECLARED` | floor playbook — não multi-agent (§16) |
| `codex` | `playbook` apenas | — | `DECLARED` | §88: não fingir subagent — playbook |
| `generic` | nada | — | `DECLARED` | floor |

Capacidades hoje em `_MEASURED_CAPABILITIES` declaram `spawn_agent: true`
para claude_code/devin_* — isso é **capacidade de plataforma declarada**,
não adapter provado. A wave separa os dois conceitos: `capabilities`
(declarado, de parity.yaml) vs `status` (provado, de execução real).

## 3. Gaps que esta wave fecha

| Gap | Seção | Entrega |
|---|---|---|
| Zero adapters — protocolo órfão | §11–22 | `agentic/runtimes/` + registry + status |
| Spawn result sem mode/usage/trace | §17–19 | `AgentSpawnResult` v2 + `ExecutionMode` fechado |
| Nenhuma engine liga gate→adapter→schema | §24–33 | execution engine canonical flow |
| Schemas de output por role inexistem | §96–104 | `agentic/schemas.py` + `contract_violation` |
| Handoff não conecta execuções reais | §40–42 | receiver re-filter + confused-deputy test |
| Case state/checkpoint sem agents | §45–48 | `CaseState` + resume por fingerprint |
| Taxonomia de falha/fallback ausente | §77–86 | failure taxonomy + ordem explícita |
| Zero medida de valor de agente | §50–75 | `evals/agent_runtime/` A/B + value vector |
| Status por agent é escalar | §174–175 | dims `contract/route/eval/host/value` |

## 4. Não-objetivos (§236)

Não se faz nesta wave: novos agents (§1 frota congelada), autonomia L3+,
mutação cloud, árvores recursivas de agents, orquestração multi-host
distribuída, e **segundo host antes do primeiro estar verde** (§230).
