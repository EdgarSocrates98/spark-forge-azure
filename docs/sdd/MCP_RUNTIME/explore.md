---
sdd: 1
feature: MCP_RUNTIME
phase: explore
profile: dev
status: done
approaches:
  - id: A1
    summary: Servidor MCP real sobre o SDK oficial `mcp` (Server low-level), com dispatch próprio resolução→autorização→validação→handler→trust→span sobre o registry declarativo existente
    tradeoffs:
      - SDK carrega handshake/ping/cancel/notifications; repo carrega tools/list, tools/call, schemas e política
      - stdio primeiro; streamable HTTP via `server.streamable_http_app()` é opcional porque starlette/uvicorn já estão instalados
  - id: A2
    summary: JSON-RPC manual sobre stdio (sem SDK)
    tradeoffs:
      - reimplementa handshake, versões de protocolo e cancelamento — superfície grande de erro sem ganho
  - id: A3
    summary: FastMCP (alto nível do SDK)
    tradeoffs:
      - esconde o pipeline de dispatch; a ordem autorização→validação→trust→observabilidade fica opaca
chosen: A1
---

# Explore — MCP_RUNTIME

## Estado atual (audit)

- `sparkforge_azure/mcp/tools.py` já tem `ToolSpec`/`ToolRisk`/`authorize()`/`compact_catalog()`/`full_catalog()` e o campo `output_schema` já existe no spec.
- `sparkforge_azure/observability/context_ledger.py` já aceita `channel`/`transport` e lê `_trust` do resultado — o ponto de instrumentação foi desenhado para MCP.
- `agentic/trust.py` tem `tool_result_envelope()` que rotula `TOOL_OUTPUT` + `DATA_ONLY` + taint.
- `evals/mcp-conformance/matrix.yaml` registra honestamente `unresolved` tudo que depende de servidor de protocolo.
- SDK instalado: `mcp` 2.3.0 no `.venv` — `Server`, `stdio_server`, `stdio_client`, `create_client_server_memory_streams`, `streamable_http_app`; starlette+uvicorn presentes.

## O que falta

Servidor de protocolo real, dispatch, entry points (stdio via `python -m sparkforge_azure.mcp` e CLI), output schemas declarados onde útil, validação jsonschema de entrada e saída, cliente real em teste, e atualização honesta da matriz.
