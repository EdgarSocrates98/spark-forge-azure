---
sdd: 1
feature: MCP_RUNTIME
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_RUNTIME/define.md
  sha256: "333d07f12983132cf0222fa0aa8cc9d937160d9d6678cf6602d48d3bd5bdf3e4"
files:
  - {path: sparkforge_azure/mcp/server.py, action: create, reason: "Server real do SDK mcp: identity + handlers list/call + validation + trust + observability; serve_http() monta o streamable_http_app do SDK"}
  - {path: sparkforge_azure/mcp/dispatch.py, action: create, reason: "pipeline puro resolution→authorization→input validation→handler→output validation→trust→span→CallToolResult, testável sem transporte"}
  - {path: sparkforge_azure/mcp/__main__.py, action: create, reason: "stdio entry: python -m sparkforge_azure.mcp"}
  - {path: sparkforge_azure/cli/cmd_mcp.py, action: create, reason: "sparkforge-azure mcp catalog|serve --transport stdio|http"}
  - {path: sparkforge_azure/cli/main.py, action: modify, reason: "registrar cmd_mcp em COMMAND_MODULES"}
  - {path: sparkforge_azure/mcp/tools.py, action: modify, reason: "tags no decorator; output_schema por tool onde útil"}
  - {path: sparkforge_azure/mcp/builtin_tools.py, action: modify, reason: "output_schema declarado"}
  - {path: sparkforge_azure/mcp/governance_tools.py, action: modify, reason: "output_schema declarado"}
  - {path: sparkforge_azure/mcp/graph_tools.py, action: modify, reason: "output_schema declarado"}
  - {path: sparkforge_azure/mcp/tokensave_tools.py, action: modify, reason: "output_schema declarado + tags returns_source"}
  - {path: tests/test_mcp_server.py, action: create, reason: "cliente MCP oficial em memory streams + stdio subprocess"}
  - {path: tests/test_graph_query.py, action: modify, reason: "fixture capturava TOOLS antes do import — apagava o registry nas sessões seguintes"}
  - {path: tests/test_architecture_layers.py, action: modify, reason: "declarar arestas cli→mcp, mcp→agentic, mcp→observability na medição"}
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
