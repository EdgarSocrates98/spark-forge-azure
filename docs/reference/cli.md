# Referência CLI — `sparkforge-azure`

Uma saída JSON por comando. Exit codes: `0` ok, `1` findings/blocked, `2`
usage/recusa. Flags globais: `--format {json,text}` (default json), `--version`.

Superfície travada por `docs/surface.lock.json` — mudar comando/flag exige
`python scripts/check_surface_lock.py --update` + explicação no commit.

## `sparkforge-azure version`

Identidade do engine (cli, engine, provider, domain, version). Sem flags.

## `sparkforge-azure tokensave <op>` — escada de recuperação L0–L6

Profiles: `economy` | `balanced` | `deep`. `--index` aponta o índice codeintel
(sqlite) quando um op precisa do grafo de código.

| Op | Camada | Uso |
|---|---|---|
| `search <query>` | L1 | busca literal; `--root`, `--profile`, `--index`, `--limit` |
| `symbols <path>` | L2 | símbolos de um arquivo (nomes+linhas) |
| `refs` | L2 | referências de um símbolo |
| `diff` | — | git diff limitado |
| `expand` | L3 | expansão de grafo (precisa `--index`) |
| `read <path>` | L5 | fatia limitada `--start`/`--end` |
| `context <task>` | L0–L6 | caminha a escada até contexto suficiente; `--term` repetível |

## `sparkforge-azure governance diagnose --scenario <file>`

Diagnóstico offline de um cenário de acesso Azure (Entra, binding/privileges
UC, storage credential, rede, RBAC, ACL ADLS). Saída: vereditos por camada,
causa raiz, conflitos §30, facts e findings. `--scenario` aceita JSON/YAML.

## `sparkforge-azure doctor`

Saúde da instalação sem acesso à nuvem: pacote, dependências, agentic OS,
tokensave, graphfy, skills/agents, surface lock, claims, extras opcionais,
credenciais (só presença — nunca autentica), traces, Forge Lab.
`network_calls: 0` sempre; `cloud_mutation: none`.

## `sparkforge-azure graph <op>` — Graphfy (offline)

| Op | Uso |
|---|---|
| `build` | `--root` (+ `--manifest`, `--out`, `--knowledge-root`, `--no-codeintel`, `--limit`). Grafo estático do workspace/repo |
| `query` | `--graph` + (`--kind` \| `--layer` \| `--neighbors` \| `--path FROM TO`), `--relation`, `--direction`, `--depth`, `--limit` |
| `impact` | `--graph` + `--changed` (path/node/knowledge id, repetível), `--depth` |
| `federate` | `--static`/`--live`/`--artifact`/`--knowledge-root`/`--out`/`--limit` — composição só por IDs explícitos |

## `sparkforge-azure collect <op>` — coletores read-only

| Op | Uso |
|---|---|
| `workspace-graph` | `--manifest` (+ `--export` offline ARG \| `--live`, `--out`, `--hash-principals`) |
| `resource-graph` | `--export` (+ `--out`, `--facts`, `--hash-principals`) — ingere export do Azure Resource Graph |

`--live` exige extra `azure` + auth; sem ele tudo é offline. Principais podem
ser hasheados (`--hash-principals`).

## `sparkforge-azure offline-bundle <op>`

| Op | Uso |
|---|---|
| `build` | `--out` + fatias (`--facts`, `--findings`, `--graph`, `--seed`, `--receipt`, `--config`, `--knowledge`). Bundle redigido — sem segredo, sem dump bruto |
| `verify` | `path` — verifica integridade/redação do bundle |

## Exit codes

| Código | Significado |
|---|---|
| `0` | sucesso |
| `1` | findings emitidos ou resultado bloqueado |
| `2` | uso inválido / recusa de entrada |

## Verbos planejados (ainda não implementados)

`analyze`, `judge`, `knowledge select|check`, `lab run|verify`, `agentops`,
`sdd check` aparecem como `tool_refs` em skills/agentes — são o contrato-alvo
das skills, não comandos existentes hoje. A superfície atual é a listada acima.
