---
sdd: 1
feature: MCP_RUNTIME
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_RUNTIME/explore.md
  sha256: "9e643c440899d0c9ba120c7ec220cfccc075918eff1945577f80f64715008378"
hypothesis:
  claim: "Um servidor MCP real (SDK `mcp`) sobre o registry existente torna as tools sfa_* servíveis por protocolo com autorização, validação e trust wrapping sem mudar o surface"
  prediction: "testes com cliente MCP oficial (mcp.client sobre memory streams e stdio) executam initialize, tools/list e tools/call end-to-end e provam denials de input/risco"
  experiment: "rodar tests/test_mcp_server.py + tests/test_mcp_conformance_matrix.py e a matriz atualizada"
acceptance:
  - id: AC1
    statement: "servidor MCP real expõe initialize + tools/list + tools/call via stdio com Server identity (name/version/instructions)"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_stdio_server_roundtrip}
  - id: AC2
    statement: "tools/list devolve name/description/inputSchema/outputSchema/annotations/risk _meta por tool"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_list_tools_full_declaration}
  - id: AC3
    statement: "tools/call valida arguments contra inputSchema e recusa inválido antes do handler"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_invalid_arguments_refused}
  - id: AC4
    statement: "tool desconhecida e cloud-read offline são negadas como resultado de erro (isError), nunca exceção crua"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_denials_are_error_results}
  - id: AC5
    statement: "resultado carrega structuredContent + content[] texto e envelopa trust data_only com taint"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_result_envelope_trust}
  - id: AC6
    statement: "cada chamada grava span com channel=mcp, tool, risk, status, duração e bytes no ledger"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_call_records_observability_span}
  - id: AC7
    statement: "output_schema declarado valida structuredContent; violação é erro interno reportado"
    verified_by: {kind: test, ref: tests/test_mcp_server.py::test_output_schema_violation_is_internal_error}
  - id: AC8
    statement: "matriz evals/mcp-conformance/matrix.yaml declara coberto somente o demonstrável"
    verified_by: {kind: test, ref: tests/test_mcp_conformance_matrix.py::test_matrix_is_honest}
success:
  - id: SC1
    metric: "tests/test_mcp_server.py verde e matriz MCP sem 'unresolved' para handshake/list/call/stdio/validation/trust"
    source: "pytest tests/test_mcp_server.py tests/test_mcp_conformance_matrix.py"
out_of_scope:
  - "transporte HTTP streamable (SDK oferece; opcional neste ciclo — registrado na matriz)"
  - "resources/prompts/capacidades de cliente (servidor tools-only por decisão)"
unknowns: []
change_kinds: [tool_or_verb]
---

# Define — MCP_RUNTIME

Fechar a lacuna registrada na matriz: o registry declarativo vira servidor de
protocolo real, com cliente oficial provando handshake, listagem, chamada,
validação de input/output, denial e trust envelope. Modo compacto preservado.
