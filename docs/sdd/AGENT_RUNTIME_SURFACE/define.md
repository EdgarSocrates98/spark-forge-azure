---
sdd: 1
feature: AGENT_RUNTIME_SURFACE
phase: define
profile: dev
status: done
hypothesis:
  claim: 'superficie de runtime: AgentSpan ganha campos §122; CLI expoe
    agents runtimes/runtime-inspect/execute --dry-run/compare; MCP read-only
    sfa_agents_runtimes + sfa_agents_execution_explain; doctor checa
    agent_runtime'
  prediction: dry-run mostra route+stages+mode sem executar host; surface
    lock regenerado com as 2 novas tools
  experiment: pytest tests/test_runtime_surface.py
acceptance:
- id: AC1
  statement: 'AgentSpan carrega runtime/execution_mode/spawn_id/
    output_valid/tool_calls; spans_from_execution converte receipt'
  verified_by:
    kind: test
    ref: tests/test_runtime_surface.py::test_spans_carry_runtime_fields
- id: AC2
  statement: 'agents execute <task> --runtime X devolve route+stages+
    fingerprints, dry_run=True, sem host (§149)'
  verified_by:
    kind: test
    ref: tests/test_runtime_surface.py::test_cli_dry_run
- id: AC3
  statement: 'sfa_agents_runtimes + sfa_agents_execution_explain registradas
    read-only; execution_explain nunca executa host'
  verified_by:
    kind: test
    ref: tests/test_runtime_surface.py::test_mcp_tools_readonly
- id: AC4
  statement: 'doctor agent_runtime reporta status por runtime sem rede'
  verified_by:
    kind: test
    ref: tests/test_runtime_surface.py::test_doctor_agent_runtime
success:
- id: SC1
  metric: superficie CLI+MCP+doctor expoe runtime sem execucao implicita
  source: pytest tests/test_runtime_surface.py
out_of_scope:
- execucao real via CLI (opt-in host separado)
unknowns: []
change_kinds:
- tool_or_verb
- agent_or_skill
---

# Define — AGENT_RUNTIME_SURFACE
