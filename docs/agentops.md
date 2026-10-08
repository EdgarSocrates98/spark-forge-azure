# AgentOps — inspeção de runs (prompt #106-112)

Todo run que passa pelo pipeline grava spans em `.sparkforge-azure/traces.db`
— um por estágio. Access emite `diagnose.load_bundle`, `extract`,
`notebook_scan`, `diagnose`, `rules`, `graph`, `evidence_trust`; os verticais
emitem os próprios prefixos (`fabric.*`, `stream.*`, `migration.load/
inventory/assess/compatibility/graph/plan/validate/verify/report`; tools MCP
`sfa_*` e retrievals `tokensave.*` também viram spans). Inspeção:

```bash
sparkforge-azure agentops runs                      # runs recentes
sparkforge-azure agentops inspect [--run <id>]      # spans + waste + eixos
sparkforge-azure agentops timeline [--run <id>]     # eventos ordenados
sparkforge-azure agentops critical-path [--run id]  # hotspots temporais
```

`--db` aponta outro `traces.db`. Sem `--run`, usa o run mais recente.

## O que se mede (#106)

tool calls · retries (decisions do recovery) · retrieval levels
(`detail_level` L0–L6 nos spans tokensave) · context bytes
(`payload_bytes` + `payload_basis` declarada) · latência por span ·
`unresolved` por span. **Provider tokens: `unresolved`** sem observação —
nunca estimado.

## Waste detector (#109)

`agentops inspect` devolve `waste` com `classification` honesta:

| pattern | classe | significado |
|---|---|---|
| `duplicate_tool_call` | observed | `sfa_*`/tool call repetida com mesmos args+metadata |
| `duplicate_span` | observed | qualquer outro componente repetido (query, search, collector, knowledge reload) |
| `full_read_after_index_hit` | hypothesis | L6 `read_full` após hits L1–L5 no mesmo run — span não carrega o target, então é revisão, não prova |
| `premium_model_on_simple_task` | hypothesis | metadata de roteamento sugere tier premium desnecessário |
| `empty_context_payload` | observed | bytes emitidos com `returned_count: 0` |

## Context quality (#110-111)

`diagnose` reporta `context_quality` por run: `selected` (facts emitidos),
`used`/`required`/`required_present`/`required_recall` — denominador é o
conjunto **explicitamente requerido** (`diagnosis.chain.evidence` +
`findings.evidence`), nunca o selecionado — `consumed_bytes` medidos, e
`cited` (facts alcançáveis via `evidence_paths`).

## Counterfactual (#112, eval-only)

`sparkforge_azure.azure.counterfactual.counterfactual_sweep(bundle)` remove
um artefato por vez e re-diagnostica numa cópia temporária — mede a
sensibilidade do veredito a cada evidência. Nunca alimenta veredito.

## Recovery de collectors (#121-125)

`collect --live` agora passa por `collectors/recover.py`: falha →
`failure_class` (authn/authz/network/rate_limit/unsupported/invalid/unknown)
→ `RecoveryPolicy`. Retry **só** em classes transientes (network,
rate_limit, provider unavailable). Terminal + `--fallback-export <file>` →
resposta `degraded` com `recovery.receipt.fallback` nomeado — fallback
nunca oculto.

## Memory do vertical (#116-120)

`sparkforge_azure.azure.memory.record_access_case(report, root)` persiste o
caso com `environment_fingerprint` Azure (tenant, subscription, workspace,
DBR/Spark, storage class, UC metastore — sem secrets). `retrieve_access_memory`
retorna candidatos com `wrong_environment`/`auto_reusable`: ambiente
divergente nunca é reusado automaticamente; conflitos seguem
`detect_memory_conflicts` (evidência, não similaridade lexical).
