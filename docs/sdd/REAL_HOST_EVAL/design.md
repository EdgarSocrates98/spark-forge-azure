---
sdd: 1
feature: REAL_HOST_EVAL
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/REAL_HOST_EVAL/define.md
  sha256: a992b4c8f900a77faeaadd2a8736c4b8bce5de056f5ca24b55cf9425059e982e
files:
- path: sparkforge_azure/agentic/agent_eval.py
  action: modify
  reason: 'evaluate_case_host: config B real — prompt materializado, spawn
    via adapter host, output parseado (JSON ou freeform→provisional),
    quality vector vs expected'
- path: scripts/run_agent_host_eval.py
  action: create
  reason: 'runner opt-in: requer SPARKFORGE_AZURE_HOST_EXECUTION=1, grava
    evals/agent_runtime/reports/<case>.host.json'
- path: sparkforge_azure/agentic/freeze.py
  action: modify
  reason: 'critical_specialists_evaluated: met quando os 4 host reports
    existem com cost medido'
- path: tests/test_host_eval.py
  action: create
  reason: contrato dos ACs (sem chamar host de verdade — dry-run do shape)
decisions:
- id: D1
  choice: 'prompt do specialist e materializado pelo proprio eval:
    task + expected schema JSON + "reply ONLY with JSON" — RoleContextPlan
    minimo (task + unresolved + schema, sem transcript de case)'
  rejected:
  - mandar o case inteiro em YAML (viola contexto minimo §28)
  - deixar o host escrever verified findings (§32 proibe)
  rollback: remover evaluate_case_host + runner + reports host
covers:
- part: real_host_eval
  acceptance: [AC1, AC2, AC3]
---

# Design — REAL_HOST_EVAL

`evaluate_case_host` monta `AgentSpawnRequestV2` com task + schema
`specialist_result` em texto; spawna via `get_adapter(claude_code)`;
`postprocess` ja extrai `result` + usage measured. O texto do modelo e
tentado como JSON (`json.loads`, faixa ```` ```json ```` tolerada); se nao
parsear -> `parse_freeform` -> provisional. `structured_output` validado
por `validate_output`. `tokens`/`cost` sao measured do envelope — e se o
envelope nao trouxer, `unresolved` (nunca estimado).
