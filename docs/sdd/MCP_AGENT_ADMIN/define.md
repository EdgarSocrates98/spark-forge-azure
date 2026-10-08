---
sdd: 1
feature: MCP_AGENT_ADMIN
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_AGENT_ADMIN/explore.md
  sha256: 692b44c16e558a3736e5f96a2350534e24101eecf881b7a5be91dbe09d9cab80
hypothesis:
  claim: sfa_agents_list e sfa_agents_explain_route expoem inventario e routing read-only
    via MCP
  prediction: dispatch retorna structuredContent com trust envelope; ambas READ_ONLY
    domain=agentic
  experiment: pytest tests/test_mcp_agent_tools.py
acceptance:
- id: AC1
  statement: sfa_agents_list retorna os 40 agents com status fechado
  verified_by:
    kind: test
    ref: tests/test_mcp_agent_tools.py::test_sfa_agents_list
- id: AC2
  statement: sfa_agents_explain_route devolve as decisoes por specialist com matched_terms
    e reason
  verified_by:
    kind: test
    ref: tests/test_mcp_agent_tools.py::test_sfa_agents_explain_route
- id: AC3
  statement: ambas READ_ONLY; superficie travada atualizada; nenhuma outra tool de
    agent
  verified_by:
    kind: test
    ref: tests/test_mcp_agent_tools.py::test_agent_tools_are_read_only
success:
- id: SC1
  metric: 15 tools sfa_, todas read-only ou pre-existentes
  source: compact_catalog
out_of_scope:
- mutacao via MCP
- spawn de agent via tool
unknowns: []
change_kinds:
- tool_or_verb
- agent_or_skill
---

# Define — MCP_AGENT_ADMIN
