# `sparkforge-azure` command reference

Generated from the real CLI parser by `doc_inventory.py` + `doc_reference.py`. Do not hand-edit generated sections — write between `keep:start`/`keep:end` markers. Status vocabulary: `available` unless marked otherwise.

## Groups

- [`agentops`](#agentops) — 5 command(s)
- [`agents`](#agents) — 10 command(s)
- [`analyze`](#analyze) — 2 command(s)
- [`collect`](#collect) — 6 command(s)
- [`context`](#context) — 2 command(s)
- [`diagnose`](#diagnose) — 3 command(s)
- [`distribution`](#distribution) — 6 command(s)
- [`doctor`](#doctor) — 1 command(s)
- [`governance`](#governance) — 2 command(s)
- [`graph`](#graph) — 5 command(s)
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

## analyze

### `analyze`

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

## install

### `install`

**Syntax**

```text
sparkforge-azure install [help] [op] [scope] [root] [host] [profile] [yes] [dry_run] [purge] [to] [repo]
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
| `dry_run` | no | — | — |
| `purge` | no | — | uninstall: also delete .sparkforge-azure state |
| `to` | no | — | update: pinned version — never 'latest' |
| `repo` | no | — | — |

<!-- keep:start -->
_free notes — errors, examples, next steps (hand-written, preserved)_
<!-- keep:end -->

## judge

### `judge`

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
