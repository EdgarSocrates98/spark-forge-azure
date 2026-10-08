"""Despacho puro de tools/call — a unidade testavel sem transporte.

A cadeia por chamada, nesta ordem (cada degrau tem recusa nomeada):

    resolucao -> autorizacao -> validacao de input -> handler
              -> validacao de output -> trust wrap -> span de observabilidade
              -> CallToolResult

NADA aqui conhece stdio/HTTP: o `server.py` e quem liga isto ao SDK. O retorno e
um `mcp.types.CallToolResult` pronto para o fio, porque o envelope e parte do
contrato — `structuredContent` carrega o payload da tool + `_trust`, e
`content[]` carrega o mesmo JSON serializado para compatibilidade.

FALHAS NUNCA VAZAM STACK. Erro de handler sai como `isError` com a classe do
erro e a mensagem truncada — a razao e acionavel, o rastro interno nao vai para
o fio. Violacao de output_schema e DEFEITO DE CONTRATO DO REPO (handler devolveu
algo fora do declarado): sai como erro `output_contract_violation` para ficar
visivel em vez de passar silenciosamente.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import jsonschema
import mcp.types as types

from sparkforge_azure.mcp.tools import ToolSpec, authorize, compact_catalog, full_catalog, load_all


@dataclass(frozen=True, slots=True)
class CallPolicy:
    """Decisões de autorização por sessão — nunca inferidas do ambiente.

    `allow_source_tools`: tools marcadas `returns_source` (tags) devolvem
    trechos de código-fonte do workspace. Sob transporte http o default é
    False — um endpoint na rede não deve vazar fonte por um endpoint aberto;
    `--allow-source-tools` no `mcp serve` reabilita explicitamente.
    """

    compact: bool = False
    allow_local_write: bool = True
    cloud_read_enabled: bool = False
    cloud_write_grant: str | None = None
    allow_source_tools: bool = True


# tools/list pagina por cursor de offset. O catálogo atual cabe numa página;
# o cursor existe para o contrato não mudar quando o catálogo crescer.
LIST_PAGE_SIZE = 100


def _registry() -> dict[str, ToolSpec]:
    return load_all()


def list_tools(*, compact: bool = False) -> list[dict[str, Any]]:
    catalog = compact_catalog() if compact else full_catalog()
    return list(catalog.values())


def tool_types(*, compact: bool = False, cursor: str | None = None) -> types.ListToolsResult:
    decls = list_tools(compact=compact)
    start = _cursor_offset(cursor)
    page = decls[start : start + LIST_PAGE_SIZE]
    next_cursor = (
        str(start + LIST_PAGE_SIZE) if start + LIST_PAGE_SIZE < len(decls) else None
    )
    return types.ListToolsResult(
        tools=[_to_tool(d) for d in page], nextCursor=next_cursor
    )


def _cursor_offset(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        return max(0, int(cursor))
    except (TypeError, ValueError):
        return 0


def _to_tool(decl: Mapping[str, Any]) -> types.Tool:
    ann = decl.get("annotations") or {}
    return types.Tool(
        name=str(decl["name"]),
        description=str(decl.get("description") or ""),
        inputSchema=dict(decl.get("inputSchema") or {"type": "object"}),
        outputSchema=dict(decl["outputSchema"]) if decl.get("outputSchema") else None,
        annotations=types.ToolAnnotations(**ann) if ann else None,
        meta=dict(decl.get("_meta") or {}),
    )


def _error_result(
    code: str, message: str, *, extra: Mapping[str, Any] | None = None
) -> types.CallToolResult:
    payload: dict[str, Any] = {
        "status": "refused" if code == "denied" else "error",
        "error": {"code": code, "message": message},
    }
    if extra:
        payload["error"].update(extra)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return types.CallToolResult(
        isError=True,
        structuredContent=payload,
        content=[types.TextContent(type="text", text=text)],
    )


def call_tool(
    name: str,
    arguments: Mapping[str, Any] | None,
    *,
    policy: CallPolicy | None = None,
    transport: str = "",
    ledger: Any = None,
) -> types.CallToolResult:
    """Despacha uma chamada de tool pelo pipeline acima. Nunca levanta."""
    policy = policy or CallPolicy()
    start = time.time()
    args = dict(arguments or {})
    spec = _registry().get(name)

    def finish(result: types.CallToolResult, outcome: str) -> types.CallToolResult:
        payload = result.structured_content if isinstance(result.structured_content, dict) else {}
        try:
            from sparkforge_azure.observability.context_ledger import shared_ledger

            (ledger or shared_ledger()).record(
                name=name,
                resultado=payload,
                detail_level="full",
                outcome=outcome,
                start_time=start,
                channel="mcp",
                transport=transport,
            )
        except Exception:  # noqa: BLE001,S110 - medicao nunca derruba a chamada
            pass
        return result

    authz = authorize(
        spec,
        allow_local_write=policy.allow_local_write,
        cloud_read_enabled=policy.cloud_read_enabled,
        cloud_write_grant=policy.cloud_write_grant,
    )
    if not authz.allowed:
        return finish(_error_result("denied", authz.reason), "unauthorized")

    assert spec is not None  # autorizado => spec existe
    if not policy.allow_source_tools and "returns_source" in spec.tags:
        return finish(
            _error_result(
                "denied",
                "tool returns workspace source; disabled under this transport: DENY",
            ),
            "unauthorized",
        )
    try:
        jsonschema.validate(args, spec.input_schema)
    except jsonschema.ValidationError as exc:
        where = ".".join(str(p) for p in exc.absolute_path)
        msg = exc.message[:240]
        return finish(
            _error_result(
                "invalid_input",
                f"arguments fail inputSchema{(' at ' + where) if where else ''}: {msg}",
            ),
            "error",
        )
    except jsonschema.SchemaError as exc:
        return finish(_error_result("invalid_schema", f"tool inputSchema invalid: {exc}"), "error")

    try:
        payload = dict(spec.handler(args))
    except Exception as exc:  # noqa: BLE001 - handler vira resultado de erro, nunca stack no fio
        return finish(
            _error_result(
                "handler_error",
                f"{type(exc).__name__}: {str(exc)[:300]}",
            ),
            "error",
        )

    if spec.output_schema is not None:
        try:
            jsonschema.validate(payload, spec.output_schema)
        except jsonschema.ValidationError as exc:
            return finish(
                _error_result(
                    "output_contract_violation",
                    f"handler result fails declared outputSchema: {exc.message[:240]}",
                ),
                "error",
            )

    from sparkforge_azure.agentic.trust import tool_result_envelope

    envelope = tool_result_envelope(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), origin=f"tool:{name}"
    )
    payload["_trust"] = {
        "label": envelope.trust.value,
        "authority": envelope.instruction_authority.value,
        "taint": envelope.taint.value,
    }
    result = types.CallToolResult(
        isError=False,
        structuredContent=payload,
        content=[
            types.TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            )
        ],
        meta={"sparkforge_azure/trust": payload["_trust"]},
    )
    return finish(result, "ok")


__all__ = ["CallPolicy", "LIST_PAGE_SIZE", "call_tool", "list_tools", "tool_types"]
