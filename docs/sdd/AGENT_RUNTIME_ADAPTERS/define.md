---
sdd: 1
feature: AGENT_RUNTIME_ADAPTERS
phase: define
profile: dev
status: done
hypothesis:
  claim: 'adapter boundary real: AgentRuntime Protocol ganha impl concreta em
    agentic/runtimes/ — registry canonico com status model §7, ExecutionMode
    fechado §17, UsageStatus §19, host stubs fail-closed honestos'
  prediction: registry expoe runtime→adapter→capabilities→status→proof;
    runtime sem prova de host classifica DECLARED_UNPROVEN, nunca HOST_PROVEN
  experiment: pytest tests/test_agentic_runtimes.py
acceptance:
- id: AC1
  statement: ExecutionMode vocab fechado {INLINE,PLAYBOOK,SEQUENTIAL_AGENT,
    PARALLEL_AGENT,SUBAGENT} e UsageStatus {measured,unresolved,not_available}
  verified_by:
    kind: test
    ref: tests/test_agentic_runtimes.py::test_closed_vocabularies
- id: AC2
  statement: 'AgentSpawnResult v2 carrega agent_id, spawn_id, runtime,
    execution_mode, status, output, structured_output, error, usage, trace_ref'
  verified_by:
    kind: test
    ref: tests/test_agentic_runtimes.py::test_spawn_result_v2_fields
- id: AC3
  statement: 'registry: todo RuntimeName resolve adapter; status model §7;
    host stubs sem prova classificam DECLARED_UNPROVEN — nunca host_proven'
  verified_by:
    kind: test
    ref: tests/test_agentic_runtimes.py::test_registry_status_honesty
- id: AC4
  statement: playbook adapter executa role deterministica INLINE de verdade
    (extractor/inventory/judge sao L0) — nao retorna "would spawn"
  verified_by:
    kind: test
    ref: tests/test_agentic_runtimes.py::test_playbook_executes_deterministic_role
- id: AC5
  statement: 'host adapter sem binario/prova: spawn_agent retorna
    runtime_unavailable explicito, nunca finge sucesso (§79 no silent
    degradation)'
  verified_by:
    kind: test
    ref: tests/test_agentic_runtimes.py::test_host_adapter_fail_closed
success:
- id: SC1
  metric: 6 runtimes no registry com status honesto; playbook executa roles
    deterministicas inline; hosts declaram sem fingir
  source: pytest tests/test_agentic_runtimes.py
out_of_scope:
- execucao real de host (sem host disponivel localmente)
- segundo host real (§230 — um primeiro, depois generaliza)
- nested agents (§208 desligado)
unknowns: []
change_kinds:
- agent_or_skill
- rule
---

# Define — AGENT_RUNTIME_ADAPTERS

Boundary §11-22: `AgenticCore → AgentRuntime protocol → HostAdapter`.
Nada de SDK de host no core (§12). Adapters host-only instalam-se em
`agentic/runtimes/`. Um adapter que retorna "would spawn" é PLAYBOOK
falso (§14) — os nossos ou executam de verdade (playbook/generic rodam
roles deterministicas inline) ou recusam com `runtime_unavailable`.
