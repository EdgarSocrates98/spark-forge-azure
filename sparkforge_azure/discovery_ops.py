# sparkforge_azure/discovery_ops.py
"""Mapa ops conceituais do install-2.0 (§6.2) -> verbos REAIS do sparkforge-azure.

Fonte unica do mapeamento: o manifesto `forge/context/v1`
(`install/service.py::_context_manifest`) e o verbo
`sparkforge-azure capabilities` emitem o MESMO mapa daqui.
"""

from __future__ import annotations

from typing import Any

CLI = "sparkforge-azure"

# Dominios publicados — os MESMOS do `domains` do manifesto
# (`install/service.py::_AZURE_DOMAINS`). `DOMAIN_PREFIXES` traduz cada nome
# publicado nos prefixos nativos (categorias de regra e segmentos do
# knowledge) que o matching mecanico resolve.
DOMAINS: tuple[str, ...] = (
    "microsoft-fabric",
    "azure-synapse",
    "adf",
    "apache-iceberg",
    "spark-streaming",
    "terraform",
    "data-quality",
)

DOMAIN_PREFIXES: dict[str, tuple[str, ...]] = {
    "microsoft-fabric": ("fabric",),
    "azure-synapse": ("synapse",),
    "adf": ("adf", "data-factory", "datafactory"),
    "apache-iceberg": ("iceberg",),
    "spark-streaming": ("streaming", "stream"),
    "terraform": ("terraform",),
    "data-quality": ("data-quality", "dq"),
}


def domain_prefixes(domain: str) -> tuple[str, ...]:
    """Os prefixos nativos de um dominio publicado; valor fora da tabela casa
    como prefixo literal normalizado."""
    norm = domain.strip().lower().replace("_", "-")
    return DOMAIN_PREFIXES.get(norm, (norm,))


PROTOCOLS: tuple[dict[str, str], ...] = (
    {"id": "forge/v1", "version": "1"},
    {"id": "forge/context/v1", "version": "1"},
    {"id": "forge/context-registry/v1", "version": "1"},
)

MCP_INTERFACE: dict[str, Any] = {
    "server_name": "sparkforge-azure",
    "command": [CLI, "mcp", "serve"],
    "verify_tool": "sfa_version",
}

OPS: dict[str, dict[str, Any]] = {
    "capabilities.list": {
        "id": "capabilities",
        "argv": ["capabilities"],
        "mode": "direct-capability",
        "description": (
            "capabilities.list (§6.2) — o que este forge instalado consegue "
            "fazer: contagens reais, dominios, protocolos e este mapa"
        ),
    },
    "protocol.describe": {
        "id": "capabilities",
        "argv": ["capabilities"],
        "mode": "direct-capability",
        "description": (
            "protocol.describe (§6.2) — secoes `protocols`+`interfaces` do "
            "mesmo verbo `capabilities`"
        ),
    },
    "rules.search": {
        "id": "rules-search",
        "argv": [
            "rules",
            "search",
            "--query",
            "{term}",
            "--category",
            "{category}",
            "--severity",
            "{severity}",
            "--limit",
            "{limit}",
            "--cursor",
            "{cursor}",
        ],
        "mode": "direct-capability",
        "description": (
            "rules.search (§6.2) — catalogo filtrado por palavra-chave, "
            "categoria, severidade; paginado, campos §6.4 completos"
        ),
    },
    "rules.get": {
        "id": "rules-get",
        "argv": ["rules", "get", "{rule_id}"],
        "mode": "direct-capability",
        "description": (
            "rules.get (§6.2) — uma regra pelo id; ausente volta vazio, "
            "nunca inventada"
        ),
    },
    "knowledge.search": {
        "id": "knowledge-search",
        "argv": [
            "knowledge",
            "search",
            "{term}",
            "--domain",
            "{domain}",
            "--limit",
            "{limit}",
            "--cursor",
            "{cursor}",
        ],
        "mode": "direct-capability",
        "description": (
            "knowledge.search (§6.2) — busca textual offline com filtro de "
            "dominio, paginacao e sha256 por documento"
        ),
    },
    "knowledge.get": {
        "id": "knowledge-get",
        "argv": ["knowledge", "get", "{file}"],
        "mode": "direct-capability",
        "description": (
            "knowledge.get (§6.2) — resolve o caminho absoluto do documento "
            "no pacote instalado, com sha256 e proveniencia"
        ),
    },
    "context.build": {
        "id": "context-pack",
        "argv": ["context", "pack", "--domain", "{domain}"],
        "mode": "direct-capability",
        "description": (
            "context.build (§6.2) — Context Pack limitado por dominio: "
            "regras aplicaveis + knowledge + protocolos + hash"
        ),
    },
    "health.check": {
        "id": "doctor",
        "argv": ["doctor"],
        "mode": "diagnostic-only",
        "description": "health.check (§6.2) — ambiente, pacote e catalogos",
    },
}


def commands() -> list[dict[str, Any]]:
    """Os `discovery.commands` do manifesto — um comando por id declarado,
    na ordem estavel das OPS (ids unicos preservados)."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for entry in OPS.values():
        if entry["id"] in seen:
            continue
        seen.add(entry["id"])
        out.append(
            {
                "id": entry["id"],
                "argv": [CLI, *entry["argv"]],
                "mode": entry["mode"],
                "read_only": True,
                "description": entry["description"],
            }
        )
    return out


def ops() -> dict[str, str]:
    """O `discovery.ops` do manifesto: op conceitual -> id do comando."""
    return {op: entry["id"] for op, entry in OPS.items()}


def ops_expanded() -> dict[str, dict[str, Any]]:
    """O mapa materializado para `capabilities`: op -> comando + argv real."""
    return {
        op: {"command": entry["id"], "argv": [CLI, *entry["argv"]]}
        for op, entry in OPS.items()
    }
