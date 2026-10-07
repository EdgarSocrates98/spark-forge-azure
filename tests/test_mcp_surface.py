"""Cobertura do que existe hoje na superficie MCP Azure.

O que ha nesta arvore e o registro declarativo (`sparkforge_azure.mcp.tools`)
com o gate `authorize` — servidor de protocolo (handshake, transporte stdio/
HTTP, envelope, eras legacy/2026-07-28) ainda nao existe, e a matriz
`evals/mcp-conformance/matrix.yaml` declara esses requisitos `unresolved`
com a razao escrita. Os testes abaixo provam o que e deste repo: declaracao,
autorizacao default-deny e o conjunto compacto.
"""

from sparkforge_azure.mcp.tools import (
    CLOUD_READ,
    READ_ONLY,
    ToolSpec,
    authorize,
    compact_catalog,
    full_catalog,
    load_all,
)


def test_declarations_carry_schema_annotations_and_risk():
    tools = load_all()
    assert tools, "o registro nao pode estar vazio"
    for name, spec in tools.items():
        assert name.startswith("sfa_"), f"{name}: prefixo fora do contrato"
        decl = spec.declaration()
        assert decl["name"] == name
        assert decl["inputSchema"], f"{name}: inputSchema ausente ou vazio"
        assert decl["description"], f"{name}: description ausente"
        assert set(decl["annotations"]) == {
            "readOnlyHint",
            "destructiveHint",
            "idempotentHint",
            "openWorldHint",
        }, f"{name}: annotations fora do vocabulario MCP"
        assert decl["_meta"]["sparkforge_azure/risk"] == spec.risk.to_dict()
        if spec.output_schema is not None:
            assert decl["outputSchema"]


def test_unknown_tool_is_denied_not_raised():
    decision = authorize(None)
    assert not decision.allowed
    assert decision.reason


def test_undeclared_risk_is_denied():
    spec = ToolSpec(
        name="sfa_fake",
        description="synthetic",
        input_schema={"type": "object"},
        handler=lambda a: {},
        risk=None,  # type: ignore[arg-type] - undeclared on purpose
        domain="test",
    )
    decision = authorize(spec)
    assert not decision.allowed
    assert "risk" in decision.reason


def test_cloud_read_denied_offline():
    spec = ToolSpec(
        name="sfa_fake_cloud",
        description="synthetic",
        input_schema={"type": "object"},
        handler=lambda a: {},
        risk=CLOUD_READ,
        domain="test",
    )
    assert not authorize(spec, cloud_read_enabled=False).allowed
    assert authorize(spec, cloud_read_enabled=True).allowed


def test_read_only_default_allowed():
    spec = ToolSpec(
        name="sfa_fake_ro",
        description="synthetic",
        input_schema={"type": "object"},
        handler=lambda a: {},
        risk=READ_ONLY,
        domain="test",
    )
    assert authorize(spec).allowed


def test_compact_subset_of_full_and_only_flagged():
    full = full_catalog()
    compact = compact_catalog()
    assert compact, "conjunto compacto nao pode ser vazio"
    assert set(compact) <= set(full)
    declared = {n for n, s in load_all().items() if s.compact}
    assert set(compact) == declared
