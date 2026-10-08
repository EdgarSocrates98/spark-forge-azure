---
sdd: 1
feature: MCP_AGENT_ADMIN
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_AGENT_ADMIN/define.md
  sha256: e56125959ce133118b1cbc7886d54b48e6188afb4f31b68da4efd4f090d58937
files:
- path: sparkforge_azure/mcp/agent_tools.py
  action: create
  reason: 2 tools read-only
- path: sparkforge_azure/mcp/tools.py
  action: modify
  reason: TOOL_MODULES + agent_tools
- path: tests/test_mcp_agent_tools.py
  action: create
  reason: contrato das tools
- path: docs/surface.lock.json
  action: modify
  reason: surface regen
- path: docs/reference/mcp-tools.md
  action: modify
  reason: doc das tools
- path: tests/test_architecture_layers.py
  action: modify
  reason: aresta mcp->agentmanifest declarada
decisions:
- id: D1
  choice: modulo novo agent_tools.py em TOOL_MODULES; handlers chamam inventory()/explain_route()
    direto
  rejected:
  - adicionar em builtin_tools (dominio errado)
  - wrapper de subprocess do CLI (lento, fragil)
  rollback: reverter o commit da feature
covers:
- part: mcp_agent_admin
  acceptance:
  - AC1
  - AC2
  - AC3
---

# Design — MCP_AGENT_ADMIN
