# Runtime Adapters (§11-22, §87-93)

`agentic/runtimes/` e o adapter boundary real:

```
Agentic Core (deterministico)
    -> AgentRuntime protocol (runtimes/base.py)
    -> HostAdapter (runtimes/{generic,playbook,host}.py)
    -> AgentSpawnResultV2 (output sempre DATA_ONLY, §29)
```

## Registry canonico

`runtime_registry()` expoe por runtime: `adapter`, `capabilities`
(declaradas — parity.yaml), `status` (provado — §7) e `proof`.
`capabilities.spawn_agent=True` diz que a plataforma oferece o mecanismo;
`status=host_proven` so existe com transcript/teste real (§9).

## Vocabularios fechados

- `EXECUTION_MODES` §17: inline | playbook | sequential_agent |
  parallel_agent | subagent
- `USAGE_STATUSES` §19: measured | unresolved | not_available
- `RUNTIME_STATUSES` §7: declared -> adapter_implemented ->
  integration_tested -> host_proven -> evaluated (+ degraded |
  unavailable)
- `FAILURE_KINDS` §81: runtime_unavailable, spawn_failed, timeout,
  rate_limit, tool_unavailable, invalid_structured_output,
  budget_exceeded, host_capability_mismatch

## Adapters

| Adapter | Runtime(s) | O que faz de verdade |
|---|---|---|
| `GenericAdapter` | generic | executa roles L0 inline via `INLINE_EXECUTORS` |
| `PlaybookAdapter` | codex, copilot_ci | mesmo executor, `execution_mode=playbook` — §16 nunca conta como multi-agent |
| `HostCLIAdapter` | claude_code, devin_cli, devin_desktop | detecta binario + opt-in `SPARKFORGE_AZURE_HOST_EXECUTION=1` (§199); ausente -> `runtime_unavailable` |

`INLINE_EXECUTORS`: extractor, inventory, judge, verifier (falsificacao
deterministica: finding sem evidence_ref cai), synthesizer (render
estruturado — candidato §221 de economy win). Roles probabilisticas sem
host devolvem `unresolved` nomeado — nunca "would spawn" (§14).

## Fallback §77

`fallback.execute_with_fallback`: preferred -> playbook -> inline; falha
transiente (timeout/rate_limit) retenta 1x; permanente degrada. Toda
degradacao carrega `degraded_reason` (§78) e trilha de attempts.
