---
sdd: 1
feature: MCP_RUNTIME
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_RUNTIME/define.md
  sha256: "8eaa90c98b55bf24a2a1f13ec64215c1ba78aa874a5723a657ed4e91166f9a50"
files:
  - {path: sparkforge_azure/mcp/server.py, action: create, reason: "Server real do SDK mcp: identity + handlers list/call + validation + trust + observability"}
  - {path: sparkforge_azure/mcp/dispatch.py, action: create, reason: "pipeline puro resolution→authorization→input validation→handler→output validation→trust→span→CallToolResult, testável sem transporte"}
  - {path: sparkforge_azure/mcp/__main__.py, action: create, reason: "stdio entry: python -m sparkforge_azure.mcp"}
  - {path: sparkforge_azure/mcp/http_app.py, action: create, reason: "streamable HTTP opcional via streamable_http_app do SDK"}
  - {path: sparkforge_azure/cli/cmd_mcp.py, action: create, reason: "sparkforge-azure mcp serve --transport stdio|http"}
  - {path: sparkforge_azure/cli/main.py, action: modify, reason: "registrar cmd_mcp em COMMAND_MODULES"}
  - {path: sparkforge_azure/mcp/tools.py, action: modify, reason: "output_schema por tool onde útil"}
  - {path: tests/test_mcp_server.py, action: create, reason: "cliente MCP oficial em memory streams + stdio subprocess"}
  - {path: evals/mcp-conformance/matrix.yaml, action: modify, reason: "marcar coberto o demonstrável, manter delegação ao SDK onde aplicável"}
decisions:
  - id: D1
    choice: "SDK low-level `Server` com handlers on_list_tools/on_call_tool, não FastMCP"
    rejected: ["FastMCP: esconde o pipeline que o prompt exige explícito"]
    rollback: "reverter dispatch.py sem tocar tools.py"
  - id: D2
    choice: "dispatch puro em dispatch.py, server.py só faz a cola com o SDK"
    rejected: ["lógica dentro do handler do SDK: impossível testar sem transporte"]
    rollback: "inline dos passos no server.py"
  - id: D3
    choice: "HTTP via streamable_http_app() do SDK, atrás de flag; stdio é o transporte primário"
    rejected: ["implementar HTTP manual: o SDK já tem e está testado"]
    rollback: "remover http_app.py e a flag"
covers:
  - {part: mcp-server, acceptance: [AC1, AC2, AC3, AC4, AC5, AC6]}
  - {part: output-schema, acceptance: [AC2, AC7]}
  - {part: matrix, acceptance: [AC8]}
---

# Design — MCP_RUNTIME

`dispatch.py` é a unidade testável: `call(name, args, policy)` retorna
`CallToolResult` completo. `server.py` constrói `mcp.server.Server` com
`on_list_tools`/`on_call_tool` ligando ao dispatch. `authorize()` do registry
segue intacto; a camada nova só adiciona validação de schema, envelope de trust
(`agentic.trust.tool_result_envelope`) e span no `shared_ledger()`.
