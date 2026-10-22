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


# ---------------------------------------------------------------------------
# §7.2 (install-2.0 ciclo 5, lf-0038) — ops de evals/verification.
#
# `DISCOVERY_OPS` do `_forgecontext.py` canonico e um vocabulario FECHADO com
# os oito ops do §6.2 — `evals.*`/`verification.*` nao podem entrar em
# `discovery.ops` sem alterar o modulo vendored de outra forja (the-forge e
# o dono). O que o manifesto publica e o que o schema aceita: estes seis ops
# viram `discovery.commands` (`eval_commands()` abaixo) com o nome conceitual
# na descricao, e o verbo `capabilities` os expoe em
# `capabilities.evals.ops` via `eval_ops_expanded()` — mesmo padrao de fonte
# unica, superficie correta para cada um.
#
# `evals.result`/`verification.plan` nao sao read_only: result pode gravar o
# scorecard na execucao e plan grava o plano de acao do cenario. O fluxo
# §7.4 plan->run->evidence e o Forge Lab: `lab plan` compila o plano,
# `lab run --execute --confirm` executa (guarda do lab) e `lab inspect`/
# `lab reproduce` registram e verificam a evidencia; `lab verify` e a
# verificacao offline autorizada que o op expoe.
# ---------------------------------------------------------------------------

EVAL_OPS: dict[str, dict[str, Any]] = {
    "evals.list": {
        "id": "evals-list",
        "argv": ["evals", "list"],
        "mode": "direct-capability",
        "read_only": True,
        "description": (
            "evals.list (§7.2) — inventario classificado das suites nas 4 "
            "categorias do §7.1 (developer, runtime-decision, "
            "output-verification, host-conformance)"
        ),
    },
    "evals.describe": {
        "id": "evals-describe",
        "argv": ["evals", "describe", "--suite", "{suite}"],
        "mode": "direct-capability",
        "read_only": True,
        "description": (
            "evals.describe (§7.2) — metadados da suite: categoria, ambiente, "
            "selagem §7.3 e sha256 de integridade; gabarito selado nunca sai"
        ),
    },
    "evals.run": {
        "id": "evals-run",
        "argv": ["evals", "run", "--suite", "{suite}"],
        "mode": "direct-capability",
        "read_only": True,
        "description": (
            "evals.run (§7.2) — executa o runner deterministico da suite; "
            "suites de host recusam EVALS-REQUIRES-HOST (executor != avaliador)"
        ),
    },
    "evals.result": {
        "id": "evals-result",
        "argv": ["evals", "result", "--suite", "{suite}", "--run", "{run}"],
        "mode": "direct-capability",
        "read_only": False,
        "description": (
            "evals.result (§7.2) — scorecard de uma execucao de host gravada "
            "(grava scorecard.json na execucao quando ausente)"
        ),
    },
    "verification.plan": {
        "id": "verification-plan",
        "argv": ["lab", "plan", "{scenario}"],
        "mode": "direct-capability",
        "read_only": False,
        "description": (
            "verification.plan (§7.2/§7.4) — compila o plano de verificacao "
            "do cenario Forge Lab (acoes, contratos, evidencias esperadas)"
        ),
    },
    "verification.run": {
        "id": "verification-run",
        "argv": ["lab", "verify"],
        "mode": "direct-capability",
        "read_only": True,
        "description": (
            "verification.run (§7.2/§7.4) — verificacao offline autorizada: "
            "registry + cenarios + contratos; falhas e unresolved explicitos. "
            "Evidencia de execucao: `lab run --execute --confirm` + "
            "`lab inspect`/`lab reproduce --receipt`"
        ),
    },
}


def eval_commands() -> list[dict[str, Any]]:
    """Os `discovery.commands` do §7.2 — ids com hifen (o ITEM_ID_RE nao
    aceita ponto); o nome conceitual fica na descricao."""
    return [
        {
            "id": entry["id"],
            "argv": [CLI, *entry["argv"]],
            "mode": entry["mode"],
            "read_only": entry["read_only"],
            "description": entry["description"],
        }
        for entry in EVAL_OPS.values()
    ]


def eval_ops_expanded() -> dict[str, dict[str, Any]]:
    """O mapa §7.2 materializado para `capabilities.evals.ops`."""
    return {
        op: {
            "command": entry["id"],
            "argv": [CLI, *entry["argv"]],
            "read_only": entry["read_only"],
        }
        for op, entry in EVAL_OPS.items()
    }
