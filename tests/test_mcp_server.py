"""Integration do servidor MCP real — cliente oficial do SDK + transporte
in-memory, exercitando o protocolo de ponta a ponta (initialize -> list_tools
-> call_tool), e o dispatch puro sem transporte.

`InMemoryTransport` roda o `Server` real num task group e entrega streams do
`ClientSession`: o que passa aqui e protocolo JSON-RPC de verdade, nao stub.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("mcp", reason="extra [mcp] nao instalado")

import anyio
from mcp.client._memory import InMemoryTransport
from mcp.client.session import ClientSession

from sparkforge_azure.mcp.dispatch import CallPolicy, call_tool, tool_types
from sparkforge_azure.mcp.server import SERVER_NAME, build_server


def _session(policy: CallPolicy | None = None):
    server = build_server(policy, transport="test")
    return InMemoryTransport(server)


def test_stdio_server_roundtrip_initialize_list_call():
    """initialize -> tools/list -> tools/call via protocolo real do SDK."""

    async def run() -> None:
        transport = _session()
        async with transport as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert init.server_info.name == SERVER_NAME
                assert init.instructions

                listed = await session.list_tools()
                names = [t.name for t in listed.tools]
                assert names == sorted(names)
                assert "sfa_version" in names
                assert all(n.startswith("sfa_") for n in names)
                by_name = {t.name: t for t in listed.tools}
                # outputSchema declarado vai no fio junto do inputSchema
                assert by_name["sfa_version"].output_schema is not None
                assert by_name["sfa_version"].output_schema.get("type") == "object"
                # risk/dieta trafegam via _meta e annotations
                assert by_name["sfa_version"].meta["sparkforge_azure/risk"]["read_only"] is True
                assert by_name["sfa_version"].annotations is not None

                result = await session.call_tool("sfa_version", {})
                assert result.is_error is False
                assert result.structured_content["provider"] == "azure"
                assert result.structured_content["_trust"]["authority"] == "data_only"
                # canal text espelha o structuredContent (contrato legado)
                text_payload = json.loads(result.content[0].text)
                assert text_payload["provider"] == "azure"

    anyio.run(run)


def test_discover_era_served_by_sdk():
    """`server/discover` é a era moderna (2026-07-28): o client SDK faz
    discover() como primeira chamada e o server negocia a versão. Nesta era
    `ping`/`initialize` não existem no spec — quem chama recebe
    Method not found, que é a resposta correta."""

    async def run() -> None:
        transport = _session()
        async with transport as (read, write):
            async with ClientSession(read, write) as session:
                discover = await session.discover()
                assert discover is not None
                listed = await session.list_tools()
                assert any(t.name == "sfa_version" for t in listed.tools)
                result = await session.call_tool("sfa_version", {})
                assert result.is_error is False
                assert result.structured_content["provider"] == "azure"

    anyio.run(run)


def test_ping_on_initialize_era():
    """`ping` existe até a versão 2025-11-25 (era handshake)."""

    async def run() -> None:
        transport = _session()
        async with transport as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.send_ping()

    anyio.run(run)


def test_unknown_tool_returns_error_result_not_crash():
    async def run() -> None:
        transport = _session()
        async with transport as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("sfa_nao_existe", {})
                assert result.is_error is True
                assert result.structured_content["error"]["code"] == "denied"
                assert "unknown tool" in result.structured_content["error"]["message"]

    anyio.run(run)


def test_invalid_arguments_refused_before_handler():
    result = call_tool("sfa_tokensave_search", {})
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "invalid_input"
    assert "query" in result.structured_content["error"]["message"]


def test_wrong_type_argument_refused():
    result = call_tool("sfa_tokensave_search", {"query": 42})
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "invalid_input"


def test_cloud_read_denied_offline_allowed_when_enabled():
    denied = call_tool("sfa_collect_workspace_graph", {"manifest": {}}, policy=CallPolicy())
    assert denied.is_error is True
    assert denied.structured_content["error"]["code"] == "denied"
    assert "cloud read not enabled" in denied.structured_content["error"]["message"]

    enabled = call_tool(
        "sfa_collect_workspace_graph",
        {"manifest": {"subscriptions": []}},
        policy=CallPolicy(cloud_read_enabled=True),
    )
    # autorizado: o handler pode falhar por manifesto vazio, mas NUNCA por auth
    if enabled.is_error:
        assert enabled.structured_content["error"]["code"] != "denied"


def test_compact_policy_exposes_only_read_only_catalog():
    full = tool_types(compact=False)
    compact = tool_types(compact=True)
    assert len(compact.tools) <= len(full.tools)
    for tool in compact.tools:
        risk = (tool.meta or {}).get("sparkforge_azure/risk", {})
        assert risk.get("read_only") is True
        assert risk.get("cloud_write") is False
        assert risk.get("production_impact") is False


def test_output_schema_violation_is_named_error():
    """Handler que devolve fora do outputSchema declarado -> erro nomeado."""
    from sparkforge_azure.mcp import tools

    @tools.tool(
        name="sfa_test_bad_output",
        description="teste: declara outputSchema e viola",
        input_schema={"type": "object"},
        risk=tools.ToolRisk(read_only=True),
        domain="test",
        compact=True,
        output_schema={
            "type": "object",
            "required": ["expected_key"],
            "properties": {"expected_key": {"type": "string"}},
        },
    )
    def bad_handler(args):
        return {"wrong_key": "oops"}

    try:
        result = call_tool("sfa_test_bad_output", {})
    finally:
        tools.TOOLS.pop("sfa_test_bad_output", None)

    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "output_contract_violation"


def test_trust_envelope_present_on_success_result():
    result = call_tool("sfa_version", {})
    assert result.is_error is False
    trust = result.structured_content.get("_trust")
    assert trust is not None
    assert trust["label"] == "TOOL_OUTPUT"
    assert trust["authority"] == "data_only"
    assert trust["taint"] in {"external", "suspicious"}
    assert result.meta["sparkforge_azure/trust"] == trust


def test_observability_span_records_mcp_channel(tmp_path):
    from sparkforge_azure.observability.context_ledger import ContextLedger

    ledger = ContextLedger(db_path=tmp_path / "ctx.db")
    call_tool("sfa_version", {}, transport="stdio", ledger=ledger)
    spans = ledger.spans_of(ledger.run_id)
    assert spans, "dispatch deve registrar span"
    last = spans[-1]
    assert last["name"] == "sfa_version"
    meta = last.get("metadata") or {}
    assert meta.get("channel") == "mcp"
    assert meta.get("transport") == "stdio"
    assert last["outcome"] == "ok"
    assert last["payload_bytes"] > 0


def test_denial_also_records_span(tmp_path):
    from sparkforge_azure.observability.context_ledger import ContextLedger

    ledger = ContextLedger(db_path=tmp_path / "ctx.db")
    call_tool("sfa_nao_existe", {}, transport="stdio", ledger=ledger)
    assert ledger.spans_of(ledger.run_id)[-1]["outcome"] == "unauthorized"


def test_real_stdio_subprocess_roundtrip(tmp_path):
    """Sobe `python -m sparkforge_azure.mcp` como subprocesso e fala JSON-RPC
    por pipes — o transporte de verdade, não o stream in-memory. O cwd é
    tmp_path para que o `.sparkforge-azure/traces.db` do subprocesso não
    caia na árvore versionada (o backstop do conftest vigia isso)."""

    async def run() -> None:
        import sys

        from mcp.client.stdio import StdioServerParameters, stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "sparkforge_azure.mcp"],
            cwd=str(tmp_path),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert init.server_info.name == SERVER_NAME
                listed = await session.list_tools()
                assert any(t.name == "sfa_version" for t in listed.tools)
                result = await session.call_tool("sfa_version", {})
                assert result.is_error is False
                assert result.structured_content["provider"] == "azure"

    anyio.run(run)


def test_source_tools_denied_under_http_policy():
    """Sob transporte http sem opt-in, tools `returns_source` são DENY — um
    endpoint de rede não deve vazar fonte do workspace por default."""
    denied = call_tool(
        "sfa_tokensave_read",
        {"path": "pyproject.toml"},
        policy=CallPolicy(allow_source_tools=False),
        transport="http",
    )
    assert denied.is_error is True
    assert denied.structured_content["error"]["code"] == "denied"
    assert "source" in denied.structured_content["error"]["message"]

    # o opt-in reabilita
    allowed = call_tool(
        "sfa_tokensave_symbols",
        {"path": "pyproject.toml"},
        policy=CallPolicy(allow_source_tools=True),
        transport="http",
    )
    if allowed.is_error:
        assert allowed.structured_content["error"]["code"] != "denied"


def test_pagination_cursor_contract():
    """Cursor de offset: página 1 sem cursor; `nextCursor` None quando cabe."""
    page = tool_types(cursor=None)
    assert page.next_cursor is None  # catálogo cabe numa página
    page2 = tool_types(cursor="0")
    assert [t.name for t in page2.tools] == [t.name for t in page.tools]
    beyond = tool_types(cursor=str(len(page.tools) + 10))
    assert beyond.tools == []
    bad = tool_types(cursor="nao-numero")
    assert [t.name for t in bad.tools] == [t.name for t in page.tools]


def test_http_app_construction_exposes_mcp_route():
    """`serve_http` monta o app Starlette do SDK com a rota /mcp. O wire em si
    é do SDK (delegated_to_sdk); aqui se prova a fiação deste repo."""
    from sparkforge_azure.mcp.server import serve_http

    app = serve_http(CallPolicy(), host="127.0.0.1", port=0)
    routes = {getattr(r, "path", "") for r in app.routes}
    assert "/mcp" in routes


def test_cli_mcp_catalog(capsys):
    from sparkforge_azure.cli.main import main

    assert main(["mcp", "catalog"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["status"] == "ok"
    assert doc["tool_count"] > 0
    assert all(t["name"].startswith("sfa_") for t in doc["tools"])

    capsys.readouterr()
    assert main(["mcp", "catalog", "--compact"]) == 0
    compact = json.loads(capsys.readouterr().out)
    assert compact["compact"] is True
    assert compact["tool_count"] <= doc["tool_count"]
