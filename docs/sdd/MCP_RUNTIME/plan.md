---
sdd: 1
feature: MCP_RUNTIME
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_RUNTIME/design.md
  sha256: "3acd4e517ec344a5d1199ecd79f2dc7e5db269f08268abbaaba1192352457b71"
tasks:
  - id: T1
    files: [sparkforge_azure/mcp/dispatch.py]
    covers: [AC2, AC3, AC4, AC5, AC6, AC7]
    test: {path: tests/test_mcp_server.py, name: test_invalid_arguments_refused_before_handler}
  - id: T2
    files: [sparkforge_azure/mcp/server.py, sparkforge_azure/mcp/__main__.py]
    covers: [AC1]
    test: {path: tests/test_mcp_server.py, name: test_stdio_server_roundtrip_initialize_list_call}
  - id: T3
    files: [sparkforge_azure/cli/cmd_mcp.py, sparkforge_azure/cli/main.py]
    covers: [AC1]
    test: {path: tests/test_mcp_server.py, name: test_cli_mcp_catalog}
  - id: T4
    files: [sparkforge_azure/mcp/tools.py, sparkforge_azure/mcp/builtin_tools.py, sparkforge_azure/mcp/governance_tools.py, sparkforge_azure/mcp/graph_tools.py, sparkforge_azure/mcp/tokensave_tools.py]
    covers: [AC2, AC7]
    test: {path: tests/test_mcp_server.py, name: test_output_schema_violation_is_named_error}
  - id: T5
    files: [evals/mcp-conformance/matrix.yaml]
    covers: [AC8]
    test: {path: tests/test_mcp_conformance_matrix.py, name: test_covered_sempre_tem_evidencia}
---

# Plan — MCP_RUNTIME
