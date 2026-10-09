# Host Execution (§23-48, §87-95)

## Fluxo canonico §24

`run_case(case, runtime=...)` em `agentic/execution.py`:

```
case -> deterministic core -> route() -> plan_pipeline -> spawn gate
     -> adapter.spawn_agent -> schema validation -> handoff admission
     -> AgentExecutionReceipt (§28)
```

## Contratos

- **§25** `_spawn_request` resolve manifest + role plan + autonomy +
  budget antes de qualquer spawn.
- **§27/§38** estagios recebem estado acumulado (proposed_findings,
  prior_unresolved) — nunca transcript cru.
- **§31-32** output freeform -> `provisional_agent_output`; nada vira
  verified sem verificacao deterministica.
- **§40-42** handoff entre estagios via `admit_handoff` com plano do
  receptor; authority sempre DATA_ONLY.
- **§45-48** `CaseState` + `stage_fingerprint` (agent+manifest+plan+
  context+runtime) + resume: fingerprint identico nao re-executa.

## Host real

`HostCLIAdapter._run_host` so roda com binario no PATH e
`SPARKFORGE_AZURE_HOST_EXECUTION=1`. Sem prova, o host permanece
`adapter_implemented` — nunca `host_proven` (§9, §154).

## Prova gravada (cycle 10)

`claude_code` tem transcript real: `evals/host_proof/claude_code.json` —
ping minimo via `claude -p --output-format json`, `status=completed`,
`trace_ref sha256:1d1c…`, usage **measured** (cost_usd=0.66). Estado
resultante: `claude_code host_proven via evals/host_proof/claude_code.json`.
O adapter
deriva `status`/`proof` do artefato: transcript valido promove a
`host_proven`; ausente/invalido nunca promove. `ClaudeCodeAdapter.
postprocess` extrai `result` e usage do envelope JSON — tokens e custo
passam a ser `measured`, nao `unresolved`. Os 4 evals host de specialist
(config B) gravaram `evals/agent_runtime/reports/<case>.host.json` —
$2.79 total medido, necessity USEFUL x4.

## Reprodutibilidade §93

Probabilistico nao e byte-identico: avaliamos conformidade de contrato,
evidencia requerida, decisao e invariantes de seguranca.
