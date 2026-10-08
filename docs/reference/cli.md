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

## `sparkforge-azure diagnose --bundle|--suite [--profile]` — vertical de acesso (Cycle 2)

Diagnóstico offline do caso Databricks/UC/ADLS sobre um case bundle
(`case.yaml` + artefatos UC/RBAC/ACL/rede/workspace). Saída: `status`,
`failure_layer`, cadeia por camada, `findings`, `access_graph`,
`evidence_paths`, `knowledge` escopado, `trust`, `overhead`, `receipt`.

| Flag | Uso |
|---|---|
| `--bundle <dir>` | um caso (`case.yaml` + artefatos) |
| `--suite <dir>` | diretório de casos; compara com o bloco `expect:` de cada `case.yaml` |
| `--profile` | `economy\|balanced\|deep` (default `balanced`) — perfil de contexto TokenSave |

Os 10 cenários do access lab estão em `tests/fixtures/access/`
(`docs/labs/access.md`).

## `sparkforge-azure diagnose fabric --bundle|--suite [--profile]` — vertical Fabric (Cycle 3)

Mesma forma do `diagnose` de acesso, sobre o case bundle Fabric
(`workspace`, `capacity`, `items`, `lakehouse`, `shortcuts`,
`connections`, `identity`, `environment`, `pipelines`, `onelake_security`).
Cadeia: env → workspace → item → OneLake → shortcut → source → lakehouse →
runtime → spark job → capacity → data factory. Saída adiciona
`fabric_graph` e `case_meta.environment_fingerprint`. Os 16 cenários do
Fabric lab estão em `tests/fixtures/fabric/` (`docs/labs/fabric.md`).

## `sparkforge-azure diagnose stream --bundle|--suite [--profile]` — vertical Streaming/RTI (Cycle 4)

Mesma forma do `diagnose` de acesso, sobre o case bundle de streaming
(`eventhubs` namespace/hubs/consumer groups + `spark` progress/
checkpoint/state + `rti` eventstream/eventhouse/activator + `events` +
`environment`). Cadeia: event_hubs_auth → event_hubs_network →
event_hubs_capacity → partitioning → consumer_group → consumer_progress →
checkpoint → state_store → schema → spark_processing → sink →
eventstream_* → eventhouse_ingestion → kql → activator_* →
cross_environment. Saída adiciona `delivery` (classificação
unresolved-first: `at_most_once_possible`/`at_least_once`/
`effectively_once`/`exactly_once_claim_supported` — nunca promove
evidência ausente a exactly-once), `stream_graph` e o lab em
`tests/fixtures/stream/` (22 cenários).

## `sparkforge-azure agentops <op>` — inspeção de runs gravadas

| Op | Uso |
|---|---|
| `runs` | lista runs gravadas (`--limit`, default 20) |
| `inspect` | detalhe de uma run (`--run <id>`, default: mais recente) |
| `timeline` | spans em ordem temporal da run |
| `critical-path` | caminho crítico da run |

`--db` aponta o `traces.db` (default `./.sparkforge-azure/traces.db`,
honrando `SPARKFORGE_AZURE_STATE_DIR`). Detalhes em `docs/agentops.md`.

## `sparkforge-azure mcp <op>` — runtime MCP

| Op | Uso |
|---|---|
| `catalog` | imprime o catálogo `sfa_*` como JSON, offline (`--compact` = só read-only) |
| `serve` | sobe o servidor MCP (`--transport stdio\|http`, default stdio) |

Guardas de `serve`: `--compact` (só catálogo read-only), `--no-local-write`
(nega tools `local_write`), `--cloud-read` (permite `cloud_read` — default
negado), `--cloud-write-grant <TOKEN>` (grant humano explícito para
`cloud_write`; o valor nunca é logado), `--allow-source-tools` (sob HTTP,
reabilita tools que devolvem fonte do workspace), `--host`/`--port`
(default `127.0.0.1:8765`).

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
| `unity-catalog` | credenciais/locations/catálogos/grants UC — export ou SDK opt-in |
| `azure-rbac` | role assignments num scope — export ou SDK opt-in |
| `adls-meta` | postura da conta ADLS + ACLs — export ou SDK opt-in |

Todo collector segue a boundary compartilhada (`collectors.base`): resposta
bruta → redação → `assert_clean` → facts; falhas classificadas viram
`unresolved` com `failure_class`, nunca erro silencioso.

`--live` exige extra `azure` + auth; sem ele tudo é offline. Principais podem
ser hasheados (`--hash-principals`).

## `sparkforge-azure lab <op>` — Forge Lab (offline)

Flag global do subcomando: `--repo` (raiz do repositório, default `.`).
`run`/`plan` compilam o plano; execução real exige `--execute --confirm`
num host do operador. Sem isso o resultado é `planned` (dry-run).

| Op | Uso |
|---|---|
| `doctor` | pré-requisitos do lab no host (docker, memória, portas) |
| `profiles` | perfis declarados e requisitos de recurso |
| `verify` | valida `lab/versions.yaml`, suíte `golden.yaml` e contratos/schemas/probes; exit 1 se inválido |
| `scenarios` | lista os cenários da suíte com fingerprints |
| `describe <id>` | cenário compilado (`ScenarioSpec.to_dict()`) |
| `plan <id>` | plano de runtime (`--backend compose\|testcontainers`, `--execute`, `--confirm`) |
| `run <id>` | plano + status; `--all` itera a suíte inteira (CI `scheduled` usa isso) |
| `inspect <path>` | `run.json` + receipt de um diretório de run |
| `analyze <path>` | resultado de run → facts/findings (unresolved: sem analyzers embarcados ainda) |
| `compare` | `--before`/`--after` — diff de dois runs |
| `promote-fixture` | `--run`/`--destination`/`--reviewed` — promove run a fixture (exige `--reviewed`) |
| `reproduce` | `--receipt` — re-emite plano a partir de um receipt |
| `up`/`down`/`shell`/`gc` | lifecycle guardado: `--project`, `--profile`, `--service`, `--execute --confirm` |

Contratos em `lab/contracts/*.schema.json`; probes primários em
`lab/probes/catalog.yaml` (fonte de verdade machine-readable, screenshot de
dashboard proibido como fonte primária).

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

`analyze`, `judge`, `knowledge select|check`, `sdd check` aparecem como
`tool_refs` em skills/agentes — são o contrato-alvo das skills, não
comandos existentes hoje. A superfície atual é a listada acima
(`agentops` e `mcp` já são implementados — ver as seções próprias).
