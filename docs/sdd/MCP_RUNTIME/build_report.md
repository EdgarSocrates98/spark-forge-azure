---
sdd: 1
feature: MCP_RUNTIME
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/MCP_RUNTIME/plan.md
  sha256: "5cbe4ecf82d42a829fe15c56e1d6de31a2a78e9900d7c82350b7fef70e3a73fc"
tasks:
  - id: T1
    status: done
    red: {command: "cd ../sfa-red-base && .venv/Scripts/python -m pytest tests/test_mcp_server.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_mcp_server.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd ../sfa-red-base && .venv/Scripts/python -m pytest tests/test_mcp_server.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_mcp_server.py -q", exit: 0}
  - id: T3
    status: done
    red: {command: "cd ../sfa-red-base && .venv/Scripts/python -m pytest tests/test_mcp_server.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_mcp_server.py::test_cli_mcp_catalog -q", exit: 0}
  - id: T4
    status: done
    red: {command: "cd ../sfa-red-base && .venv/Scripts/python -m pytest tests/test_mcp_server.py -q", exit: 2}
    green: {command: ".venv/Scripts/python -m pytest tests/test_mcp_server.py tests/test_mcp_surface.py -q", exit: 0}
  - id: T5
    status: done
    red: {command: "cd ../sfa-red-base && .venv/Scripts/python -m pytest tests/test_mcp_conformance_matrix.py -q", exit: 1}
    green: {command: ".venv/Scripts/python -m pytest tests/test_mcp_conformance_matrix.py -q", exit: 0}
claims:
  - text: "servidor MCP real serve initialize/discover + tools/list + tools/call via stdio (subprocesso) e in-memory com cliente oficial do SDK"
    evidence_ref: "tests/test_mcp_server.py"
  - text: "args inválidos recusados antes do handler; saída validada contra outputSchema declarado; violação vira output_contract_violation"
    evidence_ref: "tests/test_mcp_server.py::test_output_schema_violation_is_named_error"
  - text: "resultado carrega structuredContent + content[] JSON + _trust (TOOL_OUTPUT/data_only) e grava span channel=mcp no ledger"
    evidence_ref: "tests/test_mcp_server.py::test_trust_envelope_present_on_success_result"
  - text: "tools returns_source são DENY sob --transport http sem --allow-source-tools"
    evidence_ref: "tests/test_mcp_server.py::test_source_tools_denied_under_http_policy"
  - text: "matriz de conformidade atualizada: protocolo delegado ao SDK declarado como delegated_to_sdk, semântica do repo covered com evidência"
    evidence_ref: "evals/mcp-conformance/matrix.yaml"
change_id: "feat/cycle2-evolution"
---

# Build Report — MCP_RUNTIME

Reds registrados são runs reais num worktree da base (`b1caf70`), onde o
arquivo de teste novo falha na coleta (exit 2 — módulo `mcp.dispatch` não
existe) e a matriz nova falha por citar evidência inexistente (exit 1).

- Suite local: `pytest -q` → 2432 passed, 9 skipped.
- Surface lock regenerado: `mcp catalog`, `mcp serve` e `outputSchema` nas 9 tools.
- Arestas novas declaradas na medição (`cli→mcp`, `mcp→agentic`, `mcp→observability`).
- Fixture `graph_tools` em test_graph_query.py corrigida: snapshot antes do import esvaziava o registry.
- `ping` não existe na era 2026-07-28 (removido do spec) — Method not found é a resposta correta; matriz declara isso.
