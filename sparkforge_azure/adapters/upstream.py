"""Intake de evidencia estrangeira: o documento `sparkforge_azure/upstream-facts/v1`.

Quando um orquestrador (The Forge, ou outro motor Spark Forge) encadeia um
diagnostico de fora neste analisador, o handoff chega traduzido para este
contrato: uma lista de facts no shape nativo (`id`, `schema_version`, `kind`,
`subject`, `measures`, `attrs`, `provenance`) cuja identidade e ESTRANGEIRA e
tem que continuar visivel:

- `id` vive no namespace `upstream:` e nunca e recomputado: o `f_<sha>` nativo
  e propriedade derivada de (kind, subject, measures) em `findings.Fact`, e
  rederivar faria a observacao estrangeira parecer observada localmente.
  Por isso upstream facts ficam como dicts — nunca viram `Fact`.
- `kind` vive no namespace `upstream.`: nenhuma regra do catalogo casa com
  esses kinds, entao nenhum juizo nativo dispara sobre claim de outro motor.
- `provenance.extractor` e `theforge/handoff`, o canal de intake — nunca um
  extrator nativo (`pyspark_ast`, `notebook_scan`, ...), que lavaria a origem.
  Na admissao o intake grava `artifact`/`artifact_sha256` do arquivo consumido,
  sobrepondo o que o documento declarar: a procedencia registra o que ESTE
  motor leu.
- `attrs.upstream` carrega a procedencia do lado de la: `provider`, `run_id`,
  `node`, `item` (strings nao vazias), mais `plan_run`, `epistemic`, `claim` e
  `evidence_ids` quando o orquestrador os tem.

No Azure a entrada e o artefato `upstream.json` do case bundle
(`*/casefile.py`): os facts entram na saida `facts` do `run_case` para
evidencia, nunca no input do `judge` — transporte de evidencia, nunca de
instrucao. Chaves imperativas (`_FORBIDDEN_KEYS`) sao recusadas em qualquer
profundidade dos campos de payload — um documento upstream nao pode carregar
prompt, rota ou diretiva para este motor. Bounds sao enforcement duro:
256 KiB por documento, 128 facts.

Erros sao `UpstreamError`; os casefiles convertem em `CaseError` (exit 2 /
erro MCP), o mesmo envelope de qualquer bundle invalido.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

UPSTREAM_SCHEMA = "sparkforge_azure/upstream-facts/v1"
# Envelope do irmao AWS (sparkforge_aws/adapters/upstream.py): mesma
# estrutura, mesmo vocabulario proibido, mesmo extractor. §118 do prompt de
# paridade pede envelope de handoff COMUM — o intake aceita os dois nomes de
# schema porque o formato e identico e a proveniencia (`attrs.upstream.
# provider`) e o que distingue origem, nao o rotulo do envelope.
UPSTREAM_SCHEMA_AWS = "sparkforge_aws/upstream-facts/v1"
ACCEPTED_UPSTREAM_SCHEMAS = frozenset({UPSTREAM_SCHEMA, UPSTREAM_SCHEMA_AWS})
UPSTREAM_EXTRACTOR = "theforge/handoff"
UPSTREAM_ID_PREFIX = "upstream:"
UPSTREAM_KIND_PREFIX = "upstream."
UPSTREAM_ARTIFACT = "upstream.json"
MAX_UPSTREAM_BYTES = 256 * 1024
MAX_UPSTREAM_FACTS = 128

_UPSTREAM_KEYS = ("provider", "run_id", "node", "item")
# Mesmo vocabulario fechado do irmao AWS (adapters/upstream.py): o que
# transformaria transporte de evidencia em transporte de instrucao. Match e
# exato apos normalizacao (lowercase, `-`/` ` -> `_`), entao `plan_run` segue
# sendo chave de procedencia enquanto `plan` e recusado.
_FORBIDDEN_KEYS = frozenset(
    {
        "action",
        "actions",
        "agent",
        "command",
        "commands",
        "directive",
        "directives",
        "execute",
        "goal",
        "instruction",
        "instructions",
        "message",
        "messages",
        "objective",
        "persona",
        "plan",
        "prompt",
        "prompts",
        "request",
        "role",
        "route",
        "routes",
        "routing",
        "system",
        "task",
        "tasks",
        "tool_call",
        "workflow",
    }
)
_FACT_MAP_FIELDS = ("subject", "measures", "attrs", "provenance")


class UpstreamError(Exception):
    """O documento de upstream nao e `sparkforge_azure/upstream-facts/v1` valido."""


def _normalized_key(key: object) -> str:
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def _forbidden_key(value: object) -> str | None:
    """Primeira chave proibida numa arvore JSON, ou None. Iterativo: a
    profundidade do payload e controlada por quem escreve o documento."""
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, Mapping):
            for key, item in node.items():
                if _normalized_key(key) in _FORBIDDEN_KEYS:
                    return str(key)
                stack.append(item)
        elif isinstance(node, (list, tuple)):
            stack.extend(node)
    return None


def _check_fact(index: int, fact: object, document: Path) -> dict[str, Any]:
    """Um fact validado: o dict de entrada com `artifact`/`artifact_sha256` do
    arquivo que o intake leu (a procedencia que este motor observou)."""
    if not isinstance(fact, Mapping):
        raise UpstreamError(f"{document.name}: upstream fact {index} nao e um objeto")
    fact_id = fact.get("id")
    kind = fact.get("kind")
    provenance = fact.get("provenance")
    upstream_attrs = fact.get("attrs")
    marked = (
        isinstance(fact_id, str)
        and fact_id.startswith(UPSTREAM_ID_PREFIX)
        and isinstance(kind, str)
        and kind.startswith(UPSTREAM_KIND_PREFIX)
        and isinstance(provenance, Mapping)
        and provenance.get("extractor") == UPSTREAM_EXTRACTOR
        and isinstance(upstream_attrs, Mapping)
        and isinstance(upstream_attrs.get("upstream"), Mapping)
    )
    if not marked:
        raise UpstreamError(
            f"{document.name}: upstream fact {index} ({fact_id!r}) nao esta marcado: "
            "precisa de id em `upstream:`, kind em `upstream.`, "
            f"provenance.extractor == {UPSTREAM_EXTRACTOR!r} e attrs.upstream "
            "com a procedencia do motor de origem"
        )
    origin = cast(Mapping[str, Any], upstream_attrs)["upstream"]
    missing = [
        key for key in _UPSTREAM_KEYS if not isinstance(origin.get(key), str) or not origin[key]
    ]
    if missing:
        raise UpstreamError(
            f"{document.name}: upstream fact {index} ({fact_id!r}): attrs.upstream "
            f"sem as chaves {missing} (provider, run_id, node, item nao vazias)"
        )
    for field_name in _FACT_MAP_FIELDS:
        payload = fact.get(field_name)
        if not isinstance(payload, Mapping):
            raise UpstreamError(
                f"{document.name}: upstream fact {index} ({fact_id!r}): "
                f"{field_name!r} precisa ser um objeto"
            )
        bad = _forbidden_key(payload)
        if bad is not None:
            raise UpstreamError(
                f"{document.name}: upstream fact {index} ({fact_id!r}): {field_name} "
                f"carrega a chave {bad!r}, que transporta instrucao — o intake de "
                "upstream aceita evidencia, nunca comandos"
            )
    return dict(fact)


def read_upstream_facts(path: str | Path) -> list[dict[str, Any]]:
    """Facts de um documento `sparkforge_azure/upstream-facts/v1`, validados e
    com a procedencia do intake gravada. Ordem do documento preservada (ja e a
    ordem do handoff, que e deterministica)."""
    document = Path(path)
    if not document.is_file():
        raise UpstreamError(f"upstream: arquivo nao encontrado: {document}")
    raw = document.read_bytes()
    if len(raw) > MAX_UPSTREAM_BYTES:
        raise UpstreamError(
            f"upstream: {document.name} excede 256 KiB "
            f"({MAX_UPSTREAM_BYTES} bytes; {len(raw)} recebidos)"
        )
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise UpstreamError(f"upstream: {document.name}: JSON invalido: {exc}") from exc
    if not isinstance(data, Mapping) or data.get("schema") not in ACCEPTED_UPSTREAM_SCHEMAS:
        raise UpstreamError(
            f"upstream: {document.name}: schema precisa ser um de "
            f"{sorted(ACCEPTED_UPSTREAM_SCHEMAS)!r}"
        )
    facts = data.get("facts")
    if not isinstance(facts, list):
        raise UpstreamError(f"upstream: {document.name}: 'facts' precisa ser uma lista")
    if len(facts) > MAX_UPSTREAM_FACTS:
        raise UpstreamError(
            f"upstream: {document.name}: {len(facts)} facts excede o limite de {MAX_UPSTREAM_FACTS}"
        )
    digest = hashlib.sha256(raw).hexdigest()
    stamped: list[dict[str, Any]] = []
    for index, fact in enumerate(facts):
        checked = _check_fact(index, fact, document)
        checked["provenance"] = {
            **checked["provenance"],
            "artifact": document.name,
            "artifact_sha256": digest,
        }
        stamped.append(checked)
    return stamped


def write_upstream_facts(
    facts: list[Mapping[str, Any]],
    *,
    provider: str = "azure",
    run_id: str,
    node: str,
    consumer_schema: str = UPSTREAM_SCHEMA_AWS,
) -> dict[str, Any]:
    """Emite evidencia local no envelope comum de handoff (§118).

    O outro lado do contrato: The Forge coleta facts Azure e entrega ao
    intake do irmao. Cada fact local e EMIBRULHADO — nunca passa como nativo:

    - `id` entra sob `upstream:` (o id nativo `f_<sha>` vira suffixo);
    - `kind` entra sob `upstream.` (nenhuma regra nativa do consumidor casa);
    - `provenance.extractor` vira `theforge/handoff` — nunca o extrator real;
    - `attrs.upstream` carrega provider/run_id/node/item de quem emitiu.

    `consumer_schema` escolhe o envelope que o consumidor valida: o irmao AWS
    so aceita o proprio rotulo (`sparkforge_aws/upstream-facts/v1`), entao o
    default aponta para la — a proveniencia `provider: azure` e o que mantem
    a origem visivel dentro do envelope. Emitir para consumo proprio passe
    `consumer_schema=UPSTREAM_SCHEMA`.

    Recusa (UpstreamError) fact sem `id`/`kind` string, bounds iguais aos do
    intake, e payload que ja carregue chave de instrucao — quem emite nao
    pode empacotar o que o intake recusaria.
    """
    if not provider.strip() or not run_id.strip() or not node.strip():
        raise UpstreamError("write_upstream_facts: provider, run_id e node nao podem ser vazios")
    if consumer_schema not in ACCEPTED_UPSTREAM_SCHEMAS:
        raise UpstreamError(
            f"write_upstream_facts: consumer_schema desconhecido {consumer_schema!r} — "
            f"aceitos: {sorted(ACCEPTED_UPSTREAM_SCHEMAS)!r}"
        )
    if len(facts) > MAX_UPSTREAM_FACTS:
        raise UpstreamError(
            f"write_upstream_facts: {len(facts)} facts excede o limite de {MAX_UPSTREAM_FACTS}"
        )
    out: list[dict[str, Any]] = []
    for index, fact in enumerate(facts):
        fact_id = fact.get("id")
        kind = fact.get("kind")
        if not isinstance(fact_id, str) or not fact_id.strip():
            raise UpstreamError(f"write_upstream_facts: fact {index} sem id")
        if not isinstance(kind, str) or not kind.strip():
            raise UpstreamError(f"write_upstream_facts: fact {index} ({fact_id}) sem kind")
        subject = fact.get("subject") if isinstance(fact.get("subject"), Mapping) else {}
        measures = fact.get("measures") if isinstance(fact.get("measures"), Mapping) else {}
        attrs = dict(fact.get("attrs") or {})
        for field_name, payload in (
            ("subject", subject), ("measures", measures), ("attrs", attrs),
        ):
            bad = _forbidden_key(payload)
            if bad is not None:
                raise UpstreamError(
                    f"write_upstream_facts: fact {index} ({fact_id}): {field_name} "
                    f"carrega a chave {bad!r} — emissor nao empacota instrucao"
                )
        attrs["upstream"] = {
            "provider": provider,
            "run_id": run_id,
            "node": node,
            "item": str(fact_id),
        }
        out.append(
            {
                "id": f"{UPSTREAM_ID_PREFIX}{fact_id}",
                "schema_version": fact.get("schema_version", 1),
                "kind": f"{UPSTREAM_KIND_PREFIX}{kind}",
                "subject": dict(subject),
                "measures": dict(measures),
                "attrs": attrs,
                "provenance": {"extractor": UPSTREAM_EXTRACTOR},
            }
        )
    return {"schema": consumer_schema, "facts": out}


__all__ = [
    "ACCEPTED_UPSTREAM_SCHEMAS",
    "MAX_UPSTREAM_BYTES",
    "MAX_UPSTREAM_FACTS",
    "UPSTREAM_ARTIFACT",
    "UPSTREAM_EXTRACTOR",
    "UPSTREAM_ID_PREFIX",
    "UPSTREAM_KIND_PREFIX",
    "UPSTREAM_SCHEMA",
    "UPSTREAM_SCHEMA_AWS",
    "UpstreamError",
    "read_upstream_facts",
    "write_upstream_facts",
]
