# `sparkforge-azure` command reference

Generated from the real CLI parser by `doc_inventory.py` + `doc_reference.py`. Do not hand-edit generated sections — write between `keep:start`/`keep:end` markers. `por que`/`quando` lines come from the curated `command-rationale.json` — edit rationale there, never here. Status vocabulary: `available` unless marked otherwise.

Rationale coverage: **22/22** first-level groups curated in `command-rationale.json`.

## Groups

- [`agentops`](#agentops) — 5 command(s)
- [`agents`](#agents) — 10 command(s)
- [`ai`](#ai) — 1 command(s)
- [`analyze`](#analyze) — 2 command(s)
- [`collect`](#collect) — 6 command(s)
- [`context`](#context) — 2 command(s)
- [`diagnose`](#diagnose) — 3 command(s)
- [`distribution`](#distribution) — 6 command(s)
- [`doctor`](#doctor) — 1 command(s)
- [`governance`](#governance) — 2 command(s)
- [`graph`](#graph) — 7 command(s)
- [`install`](#install) — 1 command(s)
- [`judge`](#judge) — 1 command(s)
- [`knowledge`](#knowledge) — 2 command(s)
- [`lab`](#lab) — 17 command(s)
- [`mcp`](#mcp) — 3 command(s)
- [`migration`](#migration) — 5 command(s)
- [`offline-bundle`](#offline-bundle) — 3 command(s)
- [`sdd`](#sdd) — 3 command(s)
- [`tokensave`](#tokensave) — 9 command(s)
- [`version`](#version) — 1 command(s)
- [`workspace`](#workspace) — 6 command(s)

## agentops

### `agentops`

**para que:** inspect recorded runs: runs/inspect/timeline/critical-path

- **por que:** inspeciona runs gravadas: runs/inspect/timeline/critical-path
- **quando usar:** auditar uma execução agêntica já persistida — o que aconteceu e o caminho crítico

**Syntax**

```text
sparkforge-azure agentops [help] [db]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `db` | no | — | traces.db path (default ./.sparkforge-azure/traces.db) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agentops critical-path`

- **por que:** inspeciona runs gravadas: runs/inspect/timeline/critical-path
- **quando usar:** auditar uma execução agêntica já persistida — o que aconteceu e o caminho crítico

**Syntax**

```text
sparkforge-azure agentops critical-path [help] [run]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `run` | no | — | run_id (default: most recent) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agentops inspect`

- **por que:** inspeciona runs gravadas: runs/inspect/timeline/critical-path
- **quando usar:** auditar uma execução agêntica já persistida — o que aconteceu e o caminho crítico

**Syntax**

```text
sparkforge-azure agentops inspect [help] [run]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `run` | no | — | run_id (default: most recent) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agentops runs`

**para que:** list recorded runs

- **por que:** inspeciona runs gravadas: runs/inspect/timeline/critical-path
- **quando usar:** auditar uma execução agêntica já persistida — o que aconteceu e o caminho crítico

**Syntax**

```text
sparkforge-azure agentops runs [help] [limit]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `limit` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agentops timeline`

- **por que:** inspeciona runs gravadas: runs/inspect/timeline/critical-path
- **quando usar:** auditar uma execução agêntica já persistida — o que aconteceu e o caminho crítico

**Syntax**

```text
sparkforge-azure agentops timeline [help] [run]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `run` | no | — | run_id (default: most recent) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## agents

### `agents`

**para que:** agent fleet — list status, inspect one contract, explain a route

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents compare`

**para que:** A/B configs A-D over a case file -> frontier

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents compare [help] <case>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `case` | yes | — | path to evals/agent_runtime/cases/*.yaml |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents execute`

**para que:** dry-run do plano de execucao (nunca executa host)

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents execute [help] <task> [runtime] [max_agents] [dry_run]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `task` | yes | — | free-text case/task |
| `runtime` | no | — | — |
| `max_agents` | no | — | — |
| `dry_run` | no | — | always on — host execution is opt-in elsewhere |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents fingerprint`

**para que:** deterministic hash over the fleet's contract surface

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents fingerprint [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents impact`

**para que:** agents + test surfaces a changed path invalidates

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents impact [help] <path>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `path` | yes | — | repo-relative path changed (repeatable) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents inspect`

**para que:** full contract report for one agent

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents inspect [help] <agent_id>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `agent_id` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents list`

**para que:** status of every agent in the taxonomy

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents list [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents route`

**para que:** deterministic route explanation + spawn gate per candidate

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents route [help] <query> [max_agents] [unresolved_domain]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `query` | yes | — | free-text task/problem to route |
| `max_agents` | no | — | specialist cap (1-5, default 3) |
| `unresolved_domain` | no | — | domain with an open unresolved item (repeatable) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents runtime-inspect`

**para que:** full registry entry for one runtime

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents runtime-inspect [help] <runtime>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `runtime` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `agents runtimes`

**para que:** runtime registry: adapter, status, proof

- **por que:** frota de agentes: status, contrato individual, explicação de rota
- **quando usar:** entender quem pode executar antes de delegar uma rota

**Syntax**

```text
sparkforge-azure agents runtimes [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## ai

### `ai`

**para que:** observe AI host state (binary/version/auth/integration); --launch opens it (CLI+TTY only, never via MCP)

- **por que:** mede o host de IA (binario, versao, auth, integracao) e abre quando suportado
- **quando usar:** antes de delegar para devin/claude/codex; conferir login e integracao antes do launch (CLI+TTY)

**Syntax**

```text
sparkforge-azure ai [help] [host] [launch]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `host` | no | — | host to observe (default: all) |
| `launch` | no | — | launch the host CLI in this repo — requires a single host and a TTY |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## analyze

### `analyze`

**para que:** extract facts offline (only kinds with an extractor)

- **por que:** extrai facts offline — só os kinds que têm extrator implementado
- **quando usar:** inventário factual antes de judge/diagnose; nada roda nem assume

**Syntax**

```text
sparkforge-azure analyze [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `analyze pyspark`

**para que:** PySpark AST facts from a .py file or directory

- **por que:** extrai facts offline — só os kinds que têm extrator implementado
- **quando usar:** inventário factual antes de judge/diagnose; nada roda nem assume

**Syntax**

```text
sparkforge-azure analyze pyspark [help] <path> [out]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `path` | yes | — | file or directory to analyse |
| `out` | no | — | write {'facts': [...]} to this JSON file |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## collect

### `collect`

**para que:** read-only Azure collectors (offline exports by default)

- **por que:** coletores Azure somente-leitura; exports offline por padrão
- **quando usar:** trazer evidência do ambiente Azure para análise local

**Syntax**

```text
sparkforge-azure collect [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `collect adls-meta`

**para que:** ADLS account posture + ACLs

- **por que:** coletores Azure somente-leitura; exports offline por padrão
- **quando usar:** trazer evidência do ambiente Azure para análise local

**Syntax**

```text
sparkforge-azure collect adls-meta [help] [export] [live] [account_url] [container] [paths] [fallback_export] [facts]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `export` | no | — | offline ADLS export (JSON) |
| `live` | no | — | read ACLs via azure-storage-file-datalake |
| `account_url` | no | — | https://<acct>.dfs.core.windows.net |
| `container` | no | — | filesystem/container name |
| `paths` | no | — | paths whose ACLs to read |
| `fallback_export` | no | — | offline export to use if --live fails (degraded mode) |
| `facts` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `collect azure-rbac`

**para que:** role assignments at a scope

- **por que:** coletores Azure somente-leitura; exports offline por padrão
- **quando usar:** trazer evidência do ambiente Azure para análise local

**Syntax**

```text
sparkforge-azure collect azure-rbac [help] [export] [live] [scope] [subscription_id] [fallback_export] [facts]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `export` | no | — | offline assignments export (JSON) |
| `live` | no | — | read assignments via azure-mgmt-authorization |
| `scope` | no | — | ARM scope to list assignments for (--live) |
| `subscription_id` | no | — | subscription for --live |
| `fallback_export` | no | — | offline export to use if --live fails (degraded mode) |
| `facts` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `collect resource-graph`

**para que:** ingest an Azure Resource Graph export

- **por que:** coletores Azure somente-leitura; exports offline por padrão
- **quando usar:** trazer evidência do ambiente Azure para análise local

**Syntax**

```text
sparkforge-azure collect resource-graph [help] <export> [out] [facts] [hash_principals]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `export` | yes | — | — |
| `out` | no | — | write the live graph JSON here |
| `facts` | no | — | include the redacted facts |
| `hash_principals` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `collect unity-catalog`

**para que:** UC credentials/locations/catalogs/grants

- **por que:** coletores Azure somente-leitura; exports offline por padrão
- **quando usar:** trazer evidência do ambiente Azure para análise local

**Syntax**

```text
sparkforge-azure collect unity-catalog [help] [export] [live] [host] [workspace_id] [fallback_export] [facts]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `export` | no | — | offline UC export (JSON) |
| `live` | no | — | read the workspace via databricks-sdk |
| `host` | no | — | workspace URL (with --live) |
| `workspace_id` | no | — | numeric workspace id (with --live) |
| `fallback_export` | no | — | offline export to use if --live fails (degraded mode) |
| `facts` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `collect workspace-graph`

**para que:** live workspace graph for a manifest

- **por que:** coletores Azure somente-leitura; exports offline por padrão
- **quando usar:** trazer evidência do ambiente Azure para análise local

**Syntax**

```text
sparkforge-azure collect workspace-graph [help] <manifest> [export] [live] [out] [hash_principals]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `manifest` | yes | — | — |
| `export` | no | — | offline Azure Resource Graph export (JSON) |
| `live` | no | — | read Azure (requires azure extra + auth) |
| `out` | no | — | write the live graph JSON here |
| `hash_principals` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## context

### `context`

**para que:** workspace-scoped context resolution (target|direct|transitive|all)

- **por que:** resolução de contexto por workspace (target|direct|transitive|all)
- **quando usar:** montar o contexto certo sob escopo declarado

**Syntax**

```text
sparkforge-azure context [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `context resolve`

**para que:** resolve the relevant project set + bounded context pack for a target

- **por que:** resolução de contexto por workspace (target|direct|transitive|all)
- **quando usar:** montar o contexto certo sob escopo declarado

**Syntax**

```text
sparkforge-azure context resolve [help] [root] [target] [scope] [profile] [task]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | starting dir (default: cwd) |
| `target` | no | — | project id or path (default: workspace default_target) |
| `scope` | no | — | locality scope (default: target — never the whole workspace by omission) |
| `profile` | no | — | TokenSave budget profile (default: economy) |
| `task` | no | — | task text — engages the per-project L0→L6 ladder (default: project set only) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## diagnose

### `diagnose`

**para que:** offline access diagnosis on a case bundle

- **por que:** diagnóstico de acesso offline sobre um case bundle
- **quando usar:** AccessDenied/permissão falhando sem motivo claro — sem chamar Azure

**Syntax**

```text
sparkforge-azure diagnose [help] [bundle] [suite] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | case bundle directory (case.yaml + artifacts) |
| `suite` | no | — | directory of case bundles; checks each expect: block |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `diagnose fabric`

**para que:** Microsoft Fabric vertical: workspace/OneLake/shortcut/Spark/capacity/pipeline diagnosis

- **por que:** diagnóstico de acesso offline sobre um case bundle
- **quando usar:** AccessDenied/permissão falhando sem motivo claro — sem chamar Azure

**Syntax**

```text
sparkforge-azure diagnose fabric [help] [bundle] [suite] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | Fabric case bundle directory (case.yaml + artifacts) |
| `suite` | no | — | directory of Fabric case bundles; checks expect: |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `diagnose stream`

**para que:** Streaming vertical: Event Hubs/consumer groups/checkpoints/Structured Streaming + Fabric RTI (Eventstream/Eventhouse/Activator) diagnosis

- **por que:** diagnóstico de acesso offline sobre um case bundle
- **quando usar:** AccessDenied/permissão falhando sem motivo claro — sem chamar Azure

**Syntax**

```text
sparkforge-azure diagnose stream [help] [bundle] [suite] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | streaming case bundle directory (case.yaml + artifacts) |
| `suite` | no | — | directory of streaming case bundles; checks expect: |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## distribution

### `distribution`

**para que:** portable distribution lifecycle: inspect/init/status/doctor/detach

- **por que:** ciclo de vida de distribuição portátil: inspect/init/status/doctor/detach
- **quando usar:** empacotar e operar a forja em ambiente sem rede

**Syntax**

```text
sparkforge-azure distribution [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `distribution detach`

**para que:** remove managed integration assets (reversible)

- **por que:** ciclo de vida de distribuição portátil: inspect/init/status/doctor/detach
- **quando usar:** empacotar e operar a forja em ambiente sem rede

**Syntax**

```text
sparkforge-azure distribution detach [help] [root] [dry_run] [purge_state] [purge_cache]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | project root (default: cwd) |
| `dry_run` | no | — | report what would be removed |
| `purge_state` | no | — | also remove .sparkforge-azure state |
| `purge_cache` | no | — | also remove the managed cache dir |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `distribution doctor`

**para que:** offline portable health (no Azure auth)

- **por que:** ciclo de vida de distribuição portátil: inspect/init/status/doctor/detach
- **quando usar:** empacotar e operar a forja em ambiente sem rede

**Syntax**

```text
sparkforge-azure distribution doctor [help] [root]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | project root (default: cwd) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `distribution init`

**para que:** initialize portable identity + local integration

- **por que:** ciclo de vida de distribuição portátil: inspect/init/status/doctor/detach
- **quando usar:** empacotar e operar a forja em ambiente sem rede

**Syntax**

```text
sparkforge-azure distribution init [help] [root] [name] [with_mirrors] [regen_id]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | project root (default: cwd) |
| `name` | no | — | project name (default: directory name) |
| `with_mirrors` | no | — | also materialize agent mirrors into .claude/agents/custom + .agents/agents |
| `regen_id` | no | — | mint a new project_id (for a copied/cloned project) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `distribution inspect`

**para que:** show resolved paths, assets, hosts and identities

- **por que:** ciclo de vida de distribuição portátil: inspect/init/status/doctor/detach
- **quando usar:** empacotar e operar a forja em ambiente sem rede

**Syntax**

```text
sparkforge-azure distribution inspect [help] [root]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | project root (default: cwd) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `distribution status`

**para que:** initialization state + managed-asset drift

- **por que:** ciclo de vida de distribuição portátil: inspect/init/status/doctor/detach
- **quando usar:** empacotar e operar a forja em ambiente sem rede

**Syntax**

```text
sparkforge-azure distribution status [help] [root]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | project root (default: cwd) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## doctor

### `doctor`

**para que:** installation and capability health (no cloud access)

- **por que:** saúde de instalação e capabilities — sem acesso à nuvem
- **quando usar:** primeira linha pós-install ou quando algo falha localmente

**Syntax**

```text
sparkforge-azure doctor [help] [area]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `area` | no | — | limit to an area (repeatable) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## governance

### `governance`

**para que:** multi-layer governance (Entra/RBAC/ACL/UC/network)

- **por que:** governança multi-camada (Entra/RBAC/ACL/UC/network)
- **quando usar:** avaliar camadas de controle de acesso do lakehouse

**Syntax**

```text
sparkforge-azure governance [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `governance diagnose`

**para que:** diagnose an access scenario offline

- **por que:** governança multi-camada (Entra/RBAC/ACL/UC/network)
- **quando usar:** avaliar camadas de controle de acesso do lakehouse

**Syntax**

```text
sparkforge-azure governance diagnose [help] <scenario>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `scenario` | yes | — | scenario JSON/YAML |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## graph

### `graph`

**para que:** Graphfy: semantic/workspace graph (offline)

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `graph build`

**para que:** build the static workspace/code graph

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph build [help] <root> [manifest] [out] [knowledge_root] [no_codeintel] [limit]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | yes | — | workspace or repository root |
| `manifest` | no | — | workspace manifest (default <root>/sparkforge-azure.workspace.yaml) |
| `out` | no | — | graph JSON output (default .sparkforge-azure/graph/graph.json) |
| `knowledge_root` | no | — | merge knowledge/skills/agents from this root |
| `no_codeintel` | no | — | force the ast fallback |
| `limit` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `graph federate`

**para que:** compose static+live+artifact+knowledge by explicit ids

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph federate [help] [static] [live] [artifact] [knowledge_root] [out] [limit]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `static` | no | — | — |
| `live` | no | — | — |
| `artifact` | no | — | — |
| `knowledge_root` | no | — | — |
| `out` | no | — | — |
| `limit` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `graph impact`

**para que:** change impact of files/symbols/knowledge ids

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph impact [help] <graph> <changed> [depth]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `graph` | yes | — | — |
| `changed` | yes | — | path, node id or knowledge id |
| `depth` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `graph query`

**para que:** query a graph by kind/layer, neighbors or path

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph query [help] <graph> [kind] [layer] [NODE_ID] [['FROM', 'TO']] [relation] [direction] [depth] [limit]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `graph` | yes | — | — |
| `kind` | no | — | — |
| `layer` | no | — | — |
| `NODE_ID` | no | — | — |
| `['FROM', 'TO']` | no | — | — |
| `relation` | no | — | — |
| `direction` | no | — | — |
| `depth` | no | — | — |
| `limit` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `graph ui`

**para que:** open the local Graph Studio explorer for a graph

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph ui [help] [graph] [no_browser] [port]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `graph` | no | — | saved graph JSON (default: .sparkforge-azure/graph/graph.json) |
| `no_browser` | no | — | serve without opening a browser (SSH) |
| `port` | no | — | port to bind (default ephemeral) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `graph view`

**para que:** emit the ForgeGraphView/v1 document (Graph Studio)

- **por que:** Graphfy: grafo semântico/workspace offline
- **quando usar:** navegar relações declaradas e observadas do workspace

**Syntax**

```text
sparkforge-azure graph view [help] [graph]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `graph` | no | — | saved graph JSON (default: .sparkforge-azure/graph/graph.json) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## install

### `install`

**para que:** forge/* install lifecycle: apply/status/doctor/repair/uninstall/update/mcp-verify

- **por que:** ciclo de vida forge/*: apply/status/doctor/repair/uninstall/update/mcp-verify
- **quando usar:** instalar, reparar ou remover a integração governada

**Syntax**

```text
sparkforge-azure install [help] [op] [scope] [root] [host] [profile] [yes] [components] [dry_run] [purge] [to] [repo]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `op` | no | — | lifecycle verb (default: apply — writes managed assets) |
| `scope` | no | — | — |
| `root` | no | — | explicit target root (default: resolved from cwd) |
| `host` | no | — | — |
| `profile` | no | — | — |
| `yes` | no | — | explicit approval — required for any write |
| `components` | no | — | optional components csv: skills,agents,mcp,tui,graph-studio |
| `dry_run` | no | — | — |
| `purge` | no | — | uninstall: also delete .sparkforge-azure state |
| `to` | no | — | update: pinned version — never 'latest' |
| `repo` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## judge

### `judge`

**para que:** apply the versioned rule catalogue to facts

- **por que:** aplica o catálogo de regras versionado sobre facts
- **quando usar:** depois do analyze/collect: facts viram findings com rule_id

**Syntax**

```text
sparkforge-azure judge [help] <facts> [KEY=VERSION]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `facts` | yes | — | facts JSON (list or {'facts': [...]}) |
| `KEY=VERSION` | no | — | runtime component version, repeatable (e.g. spark=3.5.0) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## knowledge

### `knowledge`

**para que:** dated knowledge packs

- **por que:** knowledge packs datados
- **quando usar:** consultar a fonte versionada de regras e matrizes

**Syntax**

```text
sparkforge-azure knowledge [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `knowledge select`

**para que:** bounded claims from one knowledge pack

- **por que:** knowledge packs datados
- **quando usar:** consultar a fonte versionada de regras e matrizes

**Syntax**

```text
sparkforge-azure knowledge select [help] <domain> [query] [limit]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `domain` | yes | — | pack dir under knowledge/azure or knowledge |
| `query` | no | — | terms to rank claims (omit = first claims) |
| `limit` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## lab

### `lab`

**para que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab [help] [repo]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `repo` | no | — | repository root (default .) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab analyze`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab analyze [help] <path>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `path` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab compare`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab compare [help] <before> <after>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `before` | yes | — | — |
| `after` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab describe`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab describe [help] [scenario] [all] [backend] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `scenario` | no | — | scenario id (omit com --all) |
| `all` | no | — | todos os cenarios (plan/run) |
| `backend` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab doctor`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab doctor [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab down`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab down [help] [project] [profile] [service] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `project` | no | — | — |
| `profile` | no | — | — |
| `service` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab gc`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab gc [help] [project] [profile] [service] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `project` | no | — | — |
| `profile` | no | — | — |
| `service` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab inspect`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab inspect [help] <path>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `path` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab plan`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab plan [help] [scenario] [all] [backend] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `scenario` | no | — | scenario id (omit com --all) |
| `all` | no | — | todos os cenarios (plan/run) |
| `backend` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab profiles`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab profiles [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab promote-fixture`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab promote-fixture [help] <run> <destination> [reviewed]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `run` | yes | — | — |
| `destination` | yes | — | — |
| `reviewed` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab reproduce`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab reproduce [help] <receipt>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `receipt` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab run`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab run [help] [scenario] [all] [backend] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `scenario` | no | — | scenario id (omit com --all) |
| `all` | no | — | todos os cenarios (plan/run) |
| `backend` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab scenarios`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab scenarios [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab shell`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab shell [help] [project] [profile] [service] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `project` | no | — | — |
| `profile` | no | — | — |
| `service` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab up`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab up [help] [project] [profile] [service] [execute] [confirm]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `project` | no | — | — |
| `profile` | no | — | — |
| `service` | no | — | — |
| `execute` | no | — | — |
| `confirm` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `lab verify`

- **por que:** Forge Lab offline: doctor, verify, scenarios, plan/run, lifecycle
- **quando usar:** cenários reproduzíveis sem tocar o ambiente real

**Syntax**

```text
sparkforge-azure lab verify [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## mcp

### `mcp`

**para que:** MCP runtime: catalog inspection and server

- **por que:** runtime MCP: inspeção de catálogo e servidor
- **quando usar:** servir a forja via MCP ou conferir o que está exposto

**Syntax**

```text
sparkforge-azure mcp [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `mcp catalog`

**para que:** print the sfa_* tool catalog as JSON (offline)

- **por que:** runtime MCP: inspeção de catálogo e servidor
- **quando usar:** servir a forja via MCP ou conferir o que está exposto

**Syntax**

```text
sparkforge-azure mcp catalog [help] [compact]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `compact` | no | — | read-only tools only |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `mcp serve`

**para que:** run the MCP server (stdio or streamable http)

- **por que:** runtime MCP: inspeção de catálogo e servidor
- **quando usar:** servir a forja via MCP ou conferir o que está exposto

**Syntax**

```text
sparkforge-azure mcp serve [help] [transport] [compact] [no_local_write] [cloud_read] [TOKEN] [allow_source_tools] [host] [port]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `transport` | no | — | stdio is the default MCP transport |
| `compact` | no | — | expose read-only catalog only |
| `no_local_write` | no | — | deny tools declared local_write |
| `cloud_read` | no | — | allow tools declared cloud_read (default: denied) |
| `TOKEN` | no | — | explicit human grant for cloud_write tools (value is not logged) |
| `allow_source_tools` | no | — | under --transport http, re-enable tools that return workspace source |
| `host` | no | — | http bind host |
| `port` | no | — | http bind port |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## migration

### `migration`

**para que:** ADF/Synapse -> Fabric migration assessment (offline)

- **por que:** avaliação de migração ADF/Synapse -> Fabric, offline
- **quando usar:** avaliar esforço/risco de migração com evidência declarada

**Syntax**

```text
sparkforge-azure migration [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `migration assess`

**para que:** full assessment (readiness+recs+waves+validation)

- **por que:** avaliação de migração ADF/Synapse -> Fabric, offline
- **quando usar:** avaliar esforço/risco de migração com evidência declarada

**Syntax**

```text
sparkforge-azure migration assess [help] [bundle] [suite] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | migration case bundle directory |
| `suite` | no | — | directory of migration case bundles |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `migration inventory`

**para que:** estate summary + readiness census

- **por que:** avaliação de migração ADF/Synapse -> Fabric, offline
- **quando usar:** avaliar esforço/risco de migração com evidência declarada

**Syntax**

```text
sparkforge-azure migration inventory [help] [bundle] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | migration case bundle directory |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `migration plan`

**para que:** migration waves + rollback + upstream blockers

- **por que:** avaliação de migração ADF/Synapse -> Fabric, offline
- **quando usar:** avaliar esforço/risco de migração com evidência declarada

**Syntax**

```text
sparkforge-azure migration plan [help] [bundle] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | migration case bundle directory |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `migration validate`

**para que:** post-migration validation dimensions

- **por que:** avaliação de migração ADF/Synapse -> Fabric, offline
- **quando usar:** avaliar esforço/risco de migração com evidência declarada

**Syntax**

```text
sparkforge-azure migration validate [help] [bundle] [profile]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `bundle` | no | — | migration case bundle directory |
| `profile` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## offline-bundle

### `offline-bundle`

**para que:** redacted evidence bundle (no secrets, no raw dumps)

- **por que:** bundle de evidência redigido — sem segredos nem dumps crus
- **quando usar:** compartilhar o case entre hosts/forjas com segurança

**Syntax**

```text
sparkforge-azure offline-bundle [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `offline-bundle build`

- **por que:** bundle de evidência redigido — sem segredos nem dumps crus
- **quando usar:** compartilhar o case entre hosts/forjas com segurança

**Syntax**

```text
sparkforge-azure offline-bundle build [help] <out> [facts] [findings] [graph] [seed] [receipt] [config] [knowledge]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `out` | yes | — | — |
| `facts` | no | — | — |
| `findings` | no | — | — |
| `graph` | no | — | — |
| `seed` | no | — | graph node id to slice around |
| `receipt` | no | — | — |
| `config` | no | — | — |
| `knowledge` | no | — | extra knowledge id |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `offline-bundle verify`

- **por que:** bundle de evidência redigido — sem segredos nem dumps crus
- **quando usar:** compartilhar o case entre hosts/forjas com segurança

**Syntax**

```text
sparkforge-azure offline-bundle verify [help] <path>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `path` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## sdd

### `sdd`

**para que:** SDD gate — spec artifact chain check/status

- **por que:** gate SDD: checa a cadeia de artefatos de spec
- **quando usar:** conferir spec→design→plan antes de construir ou entregar

**Syntax**

```text
sparkforge-azure sdd [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `sdd check`

**para que:** validate the SDD artifact chain (all features or --feature)

- **por que:** gate SDD: checa a cadeia de artefatos de spec
- **quando usar:** conferir spec→design→plan antes de construir ou entregar

**Syntax**

```text
sparkforge-azure sdd check [help] [feature]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `feature` | no | — | check a single feature (dir name) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `sdd status`

**para que:** phase/status of every feature under docs/sdd

- **por que:** gate SDD: checa a cadeia de artefatos de spec
- **quando usar:** conferir spec→design→plan antes de construir ou entregar

**Syntax**

```text
sparkforge-azure sdd status [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## tokensave

### `tokensave`

**para que:** economical retrieval ladder (L0-L6)

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave benchmark`

**para que:** baseline vs profiles on a case corpus

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave benchmark [help] <case> [task] [term] [index]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `case` | yes | — | case corpus directory |
| `task` | no | — | task text (default: UC/ADLS case) |
| `term` | no | — | required term (repeatable) |
| `index` | no | — | code-intelligence index (sqlite) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave context`

**para que:** walk the ladder until sufficient

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave context [help] [root] [profile] [index] <task> [term]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `task` | yes | — | — |
| `term` | no | — | required term (repeatable) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave diff`

**para que:** bounded git diff

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave diff [help] [root] [profile] [index] [rev] [path]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `rev` | no | — | — |
| `path` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave expand`

**para que:** L3 graph expansion (needs --index)

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave expand [help] [root] [profile] [index] <node_id> [depth]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `node_id` | yes | — | — |
| `depth` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave read`

**para que:** L5 bounded slice

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave read [help] [root] [profile] [index] <path> [start] [end]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `path` | yes | — | — |
| `start` | no | — | — |
| `end` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave refs`

**para que:** L2 references of a symbol

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave refs [help] [root] [profile] [index] <name>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `name` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave search`

**para que:** L1 literal search

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave search [help] [root] [profile] [index] <query> [limit]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `query` | yes | — | — |
| `limit` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `tokensave symbols`

**para que:** L2 symbols of a file

- **por que:** escada de retrieval econômica L0-L6
- **quando usar:** buscar contexto pagando só o nível necessário

**Syntax**

```text
sparkforge-azure tokensave symbols [help] [root] [profile] [index] <path>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | — |
| `profile` | no | — | — |
| `index` | no | — | code-intelligence index (sqlite) |
| `path` | yes | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## version

### `version`

**para que:** print engine identity and version

- **por que:** imprime identidade e versão do engine
- **quando usar:** confirmar qual build está rodando

**Syntax**

```text
sparkforge-azure version [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## workspace

### `workspace`

**para que:** ForgeWorkspace: discover/init/add/remove/status of declared projects

- **por que:** ForgeWorkspace: discover/init/add/remove/status de projetos declarados
- **quando usar:** operar multi-projeto dentro de um workspace declarado

**Syntax**

```text
sparkforge-azure workspace [help]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `workspace add`

**para que:** declare a repository as a workspace member

- **por que:** ForgeWorkspace: discover/init/add/remove/status de projetos declarados
- **quando usar:** operar multi-projeto dentro de um workspace declarado

**Syntax**

```text
sparkforge-azure workspace add [help] [root] <path> [id] [role] [ID] [ID]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | starting dir (default: cwd) |
| `path` | yes | — | repo dir — relative to the workspace root or absolute |
| `id` | no | — | expected project_id (collision check) |
| `role` | no | — | advisory role |
| `ID` | no | — | direct dependency ids |
| `ID` | no | — | optional dependency ids |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `workspace discover`

**para que:** suggest candidate projects — reads, never writes

- **por que:** ForgeWorkspace: discover/init/add/remove/status de projetos declarados
- **quando usar:** operar multi-projeto dentro de um workspace declarado

**Syntax**

```text
sparkforge-azure workspace discover [help] [root]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | starting dir (default: cwd) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `workspace init`

**para que:** create workspace.yaml + register the host project

- **por que:** ForgeWorkspace: discover/init/add/remove/status de projetos declarados
- **quando usar:** operar multi-projeto dentro de um workspace declarado

**Syntax**

```text
sparkforge-azure workspace init [help] [root] [name]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | starting dir (default: cwd) |
| `name` | no | — | workspace name (default: directory name) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `workspace remove`

**para que:** drop a project declaration (the repository is never deleted)

- **por que:** ForgeWorkspace: discover/init/add/remove/status de projetos declarados
- **quando usar:** operar multi-projeto dentro de um workspace declarado

**Syntax**

```text
sparkforge-azure workspace remove [help] [root] <id>
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | starting dir (default: cwd) |
| `id` | yes | — | declared project id |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

### `workspace status`

**para que:** declared projects, resolution and cycles

- **por que:** ForgeWorkspace: discover/init/add/remove/status de projetos declarados
- **quando usar:** operar multi-projeto dentro de um workspace declarado

**Syntax**

```text
sparkforge-azure workspace status [help] [root]
```

| argument/flag | required | default | description |
|---|---|---|---|
| `help` | no | — | show this help message and exit |
| `root` | no | — | starting dir (default: cwd) |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->
