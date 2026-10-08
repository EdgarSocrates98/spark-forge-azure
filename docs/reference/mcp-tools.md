# Referência MCP — tools `sfa_*`

Superfície fechada: só os módulos em `mcp/tools.py::TOOL_MODULES` registram
tools; adicionar módulo muda o surface lock. Toda saída entra no envelope MCP
com `authority=data_only` — tool output é dado, nunca instrução.

## Gate de autorização (default deny)

`authorize()` em `sparkforge_azure/mcp/tools.py`:

- tool desconhecida → `DENY`
- risco não declarado / dimensão desconhecida → `DENY`
- `cloud_write`/`production_impact` → exige `cloud_write_grant` (grant humano explícito)
- `cloud_read` → exige `cloud_read_enabled` (opt-in; padrão offline)
- `local_write` → pode ser desligado por chamada

Dimensões de risco: `read_only`, `local_write`, `cloud_read`, `cloud_write`,
`security_impact`, `production_impact`. Annotations MCP derivadas: `readOnlyHint`,
`destructiveHint` (cloud_write|production_impact), `idempotentHint`, `openWorldHint`.

## Catálogo (10 tools)

| Tool | Domínio | Risco | Params |
|---|---|---|---|
| `sfa_version` | core | read_only | — |
| `sfa_tokensave_context` | tokensave | read_only | `task*` (+ `root`, `profile`, `index`, `terms`) |
| `sfa_tokensave_search` | tokensave | read_only | `query*` (+ `root`, `profile`, `limit`) |
| `sfa_tokensave_read` | tokensave | read_only | `path*` (+ `start`, `end`, `root`, `profile`) |
| `sfa_tokensave_symbols` | tokensave | read_only | `path*` (+ `root`) |
| `sfa_governance_diagnose` | governance | read_only | `scenario*` |
| `sfa_graph_query` | graph | read_only | `graph*` (+ `kind`, `layer`, `neighbors`, `relation`, `direction`, `limit`) |
| `sfa_graph_impact` | graph | read_only | `graph*`, `changed*` (+ `max_depth`) |
| `sfa_collect_workspace_graph` | graph | read_only + **cloud_read** | `manifest*` (+ `export`, `live`) |
| `sfa_diagnose_access` | access | read_only | `bundle*` (+ `profile`) |

`*` = obrigatório. `sfa_collect_workspace_graph` é a única tool que toca nuvem
(e só leitura): default-negada até `cloud_read_enabled`; com `live=false` usa
export ARG offline. `sfa_diagnose_access` é 100% offline: roda o pipeline de
diagnóstico de acesso (UC/RBAC/ACL/rede) sobre um case bundle local e devolve
`status`, `failure_layer`, findings, grafo de acesso, knowledge escopado e
receipt.

## Cobertura do vertical sem explosão (prompt 157-159)

O vertical UC/ADLS é servido por composição, não por tool-por-API:
`sfa_collect_workspace_graph` (coleta live/export unificada) → `sfa_graph_query`
(inspeção por kind/camada) → `sfa_diagnose_access` (cadeia inteira de uma vez).
Inspectors por recurso (`*_uc_inspect`, `*_adls_inspect`) duplicariam o que o
grafo já responde — recusados para manter a superfície em 10 tools.

## Compact mode

`compact_catalog()` expõe só tools `compact=True` — o mínimo que um agente
deve ver por padrão: `sfa_version`, `sfa_tokensave_context`,
`sfa_tokensave_search`, `sfa_governance_diagnose`, `sfa_graph_impact`,
`sfa_diagnose_access`.
O catálogo completo vem de `full_catalog()`.

## Protocolo

Handshake/transporte/streaming são do SDK MCP (`mcp` extra opcional); a matrix
de conformidade honesta vive em `evals/mcp-conformance/matrix.yaml`
(`delegated_to_sdk`, `unresolved`, `not_applicable` onde não implementado).
