---
sdd: 1
feature: MCP_AGENT_ADMIN
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_AGENT_ADMIN/design.md
  sha256: 7e9577a7f6af897aa99edeae4a134b608837c7ab796dadbea3f96950912969cb
tasks:
- id: T1
  files:
  - tests/test_mcp_agent_tools.py
  covers:
  - AC1
  - AC2
  - AC3
  test:
    path: tests/test_mcp_agent_tools.py
    name: test_sfa_agents_list
- id: T2
  files:
  - sparkforge_azure/mcp/agent_tools.py
  - sparkforge_azure/mcp/tools.py
  - docs/surface.lock.json
  - docs/reference/mcp-tools.md
  covers:
  - AC1
  - AC2
  - AC3
  test:
    path: tests/test_mcp_agent_tools.py
    name: test_sfa_agents_explain_route
---

# Plan — MCP_AGENT_ADMIN
