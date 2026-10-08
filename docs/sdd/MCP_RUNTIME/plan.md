---
sdd: 1
feature: MCP_RUNTIME
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_RUNTIME/design.md
  sha256: "e4a04b1304e8823bd20bd1a99e931ddc304f2a3278c063b3b94f926fe75a49c5"
tasks:
  - id: T1
    files: [sparkforge_azure/mcp/dispatch.py]
    covers: [AC2, AC3, AC4, AC5, AC6, AC7]
    test: {path: tests/test_mcp_server.py, name: test_invalid_arguments_refused}
  - id: T2
    files: [sparkforge_azure/mcp/server.py, sparkforge_azure/mcp/__main__.py, sparkforge_azure/mcp/http_app.py]
    covers: [AC1]
    test: {path: tests/test_mcp_server.py, name: test_stdio_server_roundtrip}
  - id: T3
    files: [sparkforge_azure/cli/cmd_mcp.py, sparkforge_azure/cli/main.py]
    covers: [AC1]
    test: {path: tests/test_mcp_server.py, name: test_cli_mcp_module_registered}
  - id: T4
    files: [sparkforge_azure/mcp/tools.py]
    covers: [AC2, AC7]
    test: {path: tests/test_mcp_server.py, name: test_output_schema_violation_is_internal_error}
  - id: T5
    files: [evals/mcp-conformance/matrix.yaml]
    covers: [AC8]
    test: {path: tests/test_mcp_conformance_matrix.py, name: test_matrix_is_honest}
---

# Plan — MCP_RUNTIME
