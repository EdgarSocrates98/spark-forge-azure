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

## `sparkforge-azure migration <op>` — avaliação ADF/Synapse → Fabric (Cycle 5)

| Op | Uso |
|---|---|
| `inventory --bundle` | estate summary + censo de readiness |
| `assess --bundle\|--suite` | relatório completo (readiness + recomendações + waves + validação) |
| `plan --bundle` | readiness + waves topológicas + rollback por wave |
| `validate --bundle` | dimensões de validação pós-migração |

Sobre o case bundle de migração (`estate` ADF/Synapse/Fabric/storage +
`assessment` oficial opcional + `validation` + `notebooks/`). Offline,
determinístico: identidade = ARM id/GUID (nunca display name); ausência de
assessment nunca vira READY; divergência oficial-vs-Forge vira REVIEW +
conflito explícito; ciclo de dependência vira `plan.status=REVIEW` (nunca
ordem fabricada); segredos de linked service são removidos no boundary de
extração. O lab em `tests/fixtures/migration/` cobre os 22 cenários do
prompt (SSIS bloqueado, SHIR manual, global parameters→variable library,
delta shortcut candidato, retirement→copy, shared-LS não consolidar,
row-count≠equivalência, regressão nunca é vitória, identidade errada falha,
assessment stale, conflito oficial, metadata maliciosa DATA_ONLY,
evidência insuficiente→UNRESOLVED).

## `sparkforge-azure agentops <op>` — inspeção de runs gravadas

| Op | Uso |
|---|---|
| `runs` | lista runs gravadas (`--limit`, default 20) |
| `inspect` | detalhe de uma run (`--run <id>`, default: mais recente) |
| `timeline` | spans em ordem temporal da run |
| `critical-path` | caminho crítico da run |

`--db` aponta o `traces.db` (default `./.sparkforge-azure/traces.db`,
honrando `SPARKFORGE_AZURE_STATE_DIR`). Detalhes em `docs/agentops.md`.

## `sparkforge-azure sdd <op>` — gate de spec-driven development

| Op | Uso |
|---|---|
| `check` | valida a cadeia de artefatos SDD (`define→design→plan→build_report`) de todas as features em `docs/sdd/`; `--feature <DIR>` restringe a uma |
| `status` | fase/status de cada feature (`phase`, `next_phase`, `refused`) |

Exit codes: `0` quando a cadeia está íntegra, `1` quando há recusa nomeada
(ex.: `acceptance_never_red`, `missing_upstream`). É o gate citado em
`AGENTS.md`/`CONTRIBUTING.md`.

## `sparkforge-azure agents <op>` — frota de agents

| Op | Uso |
|---|---|
| `list` | status de cada agent da taxonomia (`ready` \| `partial` \| `manifest_only` \| `broken` \| `unevaluated`) + contagens |
| `inspect` | relatório de contrato completo de um agent (`<id>`) — dimensões `manifest`…`agentops` |
| `route` | explicação determinística da rota por candidato (`selected`/`below_cap`/`no_match` + termos) + spawn gate (`SPAWN`/`SKIP`/`DEFER`); `--max-agents`, `--unresolved-domain` |
| `fingerprint` | hash determinístico (`sha256:`) sobre a superfície de contrato da frota — manifests (campos de contrato), routing table, teams, vocabulários fechados. Drift de contrato muda o hash |
| `impact` | grafo de impacto: `--path X` (repetível) → agents + superfícies de teste invalidados pelo path; path fora do grafo → `status: unresolved` + `impact_unknown:<path>` (nunca resposta vazia confiante) |

O engine é `agentic.inventory` — função pura da árvore do repo. Inspeção
apenas; nada aqui executa agent. `docs/agentic/AGENT_INVENTORY.md` é gerada
a partir dele (`scripts/gen_agent_inventory.py`).

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
agentic fleet (status por agent), tokensave, graphfy, skills/agents, surface
lock, claims, extras opcionais, credenciais (só presença — nunca autentica),
traces, Forge Lab.
`network_calls: 0` sempre; `cloud_mutation: none`.

## `sparkforge-azure ai [host]`

Mede cada host de IA — binário no PATH, versão via `--version`, login pelo
subcomando oficial de status (`devin auth status`, `claude auth status`,
`codex login status`) e a integração do repo (`install status`). O recibo
carrega só o booleano `logged_in` — a saída de auth pode listar caminhos de
credencial e nunca entra no JSON. Estados: `NOT_DETECTED`, `SUPPORTED`,
`NEEDS_LOGIN` (com `login_hint`), `READY`, `INTEGRATION_*`.

`sparkforge-azure ai` sem argumento mede todos (`all` é o seletor implícito).
`--launch` abre o CLI do host no diretório do repo — exige um host nomeado e
TTY: sem TTY ou com `all`, o recibo traz `launch_refused` e `launch_command`
para o operador colar. Lançar é fronteira humana: o MCP expõe só o painel
read-only (`sfa_ai`).

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

## `sparkforge-azure analyze <kind>` — extratores offline de facts

| Kind | Uso |
|---|---|
| `pyspark` | `--path` (arquivo `.py` ou diretório) + `--out` opcional — facts AST (`pyspark.loop`, `pyspark.chain`, `pyspark.driver_collect`, …) sem executar o código |

Só kinds com extrator existem; os demais ficam em `planned_tool_refs` das
skills. Saída: `{"facts": [...]}` (lista completa também no stdout).

## `sparkforge-azure judge` — catálogo de regras sobre facts

`--facts` (lista `[...]`, envelope `{"facts": [...]}` ou envelope de collector
com `fact_list`) + `--runtime KEY=VERSION` repetível. Regras sem
`runtime_scope` satisfeito aparecem em `skipped`, não viram finding. Exit 1
quando há findings.

## `sparkforge-azure knowledge <op>` — packs datados

| Op | Uso |
|---|---|
| `select` | `--domain` (pack sob `knowledge/azure` ou `knowledge`) + `--query`/`--limit` — claims ranqueados; cache sob o state dir |

## `sparkforge-azure rules <op>` — catálogo versionado (offline)

Leitura direta do catálogo `rules/catalog/` — sem facts, sem runtime.

| Op | Uso |
|---|---|
| `search` | filtra regras por termo/área — offline, paginado (`--cursor`) |
| `get` | uma regra por `RULE_ID` — corpo completo + `action:` |

## `sparkforge-azure capabilities` — superfície declarada

Emite o `capability list` do manifesto — ops de discovery (§6.2),
capacidades declaradas e contagem de rules/knowledge/evals. Útil para
conferir paridade CLI↔manifesto após `install`.

## `sparkforge-azure distribution <op>` — lifecycle portável

Camada de produto portável (prompt_evo_portable.md): identidade de projeto
relocável, paths centralizados, assets empacotados, hosts detectados,
detach reversível. Todos aceitam `--root` (default: cwd). Recusas são
documentos `{"status":"refused","error":{"kind":...}}` — `kind` do vocabulário
fechado em `distribution/errors.py`.

| Op | Uso |
|---|---|
| `inspect` | resolve e reporta paths (`value`+`source` por path), identidades, config efetivo com proveniência, assets com sha256, hosts detectados — sem mutação |
| `init` | cria `.sparkforge-azure/project.yaml` + entrada gerenciada em `.mcp.json` (`mcpServers.sparkforge-azure` → `sparkforge-azure mcp serve`) + bloco gerenciado em `AGENTS.md`/`CLAUDE.md`; idempotente; `--name`, `--regen-id` (nova identidade p/ cópia), `--with-mirrors` (materializa `.claude/agents/custom/` + `.agents/agents/`) |
| `status` | `uninitialized`/`initialized`/`partial`/`drifted`/`broken` + drift por asset gerenciado |
| `doctor` | saúde offline — assets, state/cache dirs, identidade, workspace, ledger, hosts (`unavailable`/`unproven` nunca falham), runtime MCP |
| `detach` | remove só assets gerenciados (ledger); `--dry-run`, `--purge-state`, `--purge-cache`; state preservado por default; `init` religa |

Estado e cache: `.sparkforge-azure/` (projeto), override por
`SPARKFORGE_AZURE_STATE_DIR` / `SPARKFORGE_AZURE_CACHE`. Nada é escrito fora
do projeto ou dos overrides explícitos.

## `sparkforge-azure install [op]` — ciclo de vida `forge/*`

Surface de instalação portátil do contrato compartilhado
(`forge/InstallReceipt/v1`, `forge/InstallationHealth/v1`) — mesmos verbos
de todo Forge irmão; `theforge install auto` delega para cá. Implementado
sobre o ledger do `distribution` (nada duplicado): apply = `init` +
espelhos de skills no ledger; uninstall = `detach` + poda de diretórios
vazios.

| Op | Uso |
|---|---|
| *(default: apply)* | escreve assets gerenciados: `project.yaml`, chave `mcpServers.sparkforge-azure` em `.mcp.json`, blocos gerenciados em `AGENTS.md`/`CLAUDE.md`, espelhos `sparkforge-azure-*` de skills — exige `--yes` (o plano é o contrato) ou `--dry-run` |
| `status` | saúde `forge/InstallationHealth/v1` — `healthy`/`degraded`/`unverified` com `repair_hint` |
| `doctor` | checks do `distribution doctor` + handshake MCP (`mcp-handshake`: PASS/FAIL/BLOCKED — BLOCKED quando o CLI não está no PATH) |
| `repair` | reescreve só drift do ledger (`missing`/`modified`) preservando conteúdo do usuário; `--dry-run` lista o drift sem tocar |
| `uninstall` | `detach` por ledger + poda de diretórios esvaziados; `--purge` remove também o estado `.sparkforge-azure/`; `--dry-run` planeja |
| `update` | `pip install --upgrade` do checkout registrado no manifesto `~/.forge`; recusa `latest`; `--to` pinado, `--repo` alternativo |
| `mcp-verify` | handshake JSON-RPC stdio do `mcp serve` (initialize → tools/list) — honesto, nunca infere por existência de arquivo |

Flags comuns: `--scope project|workspace|user` (default `project`;
`workspace` resolve pelo `workspace.yaml` e instala no projeto corrente;
`user` escreve só assets de host sob `~`, sem identidade de projeto),
`--root`, `--host claude|devin|codex|copilot|all` (restringe os espelhos),
`--profile minimal|recommended|full` (minimal = marcadores + MCP;
recommended = + espelhos de skills; full = + espelhos de agents).
Recibos `forge/InstallReceipt/v1` com `status`
`completed`/`planned`/`failed`; recusas `PortableError` → documento
`refused` com `kind` (`FORGE-INSTALL-*`).

## `sparkforge-azure portal` — UI web local opcional

Portal web local-first sobre os mesmos serviços do CLI/MCP — jornada
"instalar → configurar hosts → verificar MCP → primeira tarefa" numa SPA,
sem substituir CLI/TUI/MCP (que seguem funcionando sozinhos).

| Flag | Uso |
|---|---|
| `--port` | porta TCP fixa (default `0` = porta livre do sistema) |
| `--root` | workspace inspecionado (default: cwd) |
| `--no-browser` | só imprime a URL com o token — SSH/headless ou abertura manual |

O bind é sempre `127.0.0.1` (loopback only — o portal é local-first e
não expõe interface de rede).

**Por que:** quem prefere UI a CLI executa a mesma jornada com a mesma
segurança — sessão `X-Forge-Session` obrigatória, mutações exigem
`confirm` + `plan_token` assinado, hosts nunca são lançados
implicitamente (boundary TTY/humano). **Quando usar:** primeira
instalação da forja, revisão visual de saúde/skills/agents/grafos/docs,
e tarefas seguras com recibo. **Quando não usar:** automação/CI (use o
CLI/MCP direto — o portal é um cliente, não um serviço).

## `sparkforge-azure workspace <op>` — ForgeWorkspace

Agrupamento lógico de projetos — **não** é Azure/Databricks/Fabric
Workspace. Manifesto em `.sparkforge-azure/workspace.yaml`, data-only,
determinístico e offline. Todos aceitam `--root` (default: cwd).

| Op | Uso |
|---|---|
| `discover` | sugere candidatos (cwd, ancestrais limitados, filhos declarados e do root) — nunca escreve; `workspace add` confirma |
| `init` | cria `workspace.yaml` (`workspace_id` `sfw-*`) + registra o projeto hospedeiro como `default_target`; idempotente; `--name` |
| `add <path>` | declara repo membro: relativo ao root ou absoluto (externo = declarado explicitamente); cria a identidade portátil do alvo se ausente (`initialized_target`); `--role`, `--depends-on ID...`, `--optional ID...` |
| `remove <id>` | remove só a declaração e as arestas de entrada — nunca deleta o repositório |
| `status` | projetos declarados × resolução + `dependency_cycles`; estados `ok`/`degraded`/`dependency_cycle` |

Roles: `application|data|infra|shared|tests|docs`. Dependências declaradas
são `direct` ou `optional`; `transitive` é derivado na leitura. Identidade
nunca vem de path — `workspace add` usa o `project.yaml` do alvo.

## `sparkforge-azure context resolve` — contexto com escopo

Responde "qual contexto deste workspace é relevante para este target?".
Requer `workspace.yaml`; recusa `workspace_not_found` sem ele.

| Flag | Uso |
|---|---|
| `--target` | id ou path do projeto (default: `default_target` do workspace) |
| `--scope` | `target` (default) \| `direct` \| `transitive` \| `all` — o workspace inteiro nunca é lido por omissão; `all` é só explícito |
| `--profile` | `economy` (default) \| `balanced` \| `deep` — orçamento TokenSave |
| `--task` | texto da tarefa — engaja a escada L0→L6 por projeto; sem task, resolve só o conjunto de projetos |

Saída = recibo §58 persistido em `.sparkforge-azure/receipt-context.json`:
`projects_considered`, `projects_selected`, `files_considered`,
`files_materialized`, `bytes_read`, `bytes_avoided`, `stop_reason`
(`scope_complete`/`sufficient`/`partial`) e `unresolved`. Um projeto nunca
recebe arquivos de outro sem aresta declarada ou `all` explícito — cada
TokenSave é confinado por `resolve_within` à própria raiz. Ciclos recusam
`dependency_cycle`.

## `sparkforge-azure delegate <op>` — delegação governada a especialistas

Delegação opcional e determinística para forges irmãos —
`data-sentinel-forge` (`data-sentinel`, diagnóstico de runtime sobre
artefatos exportados: logs de driver/executor Databricks, `spark
explain`, `sql analyze`, `lakehouse metadata|operation|access|compat`
para Delta/Unity Catalog) e `forge-doctor-data` (`forge-doctor-data scan
--format agent`, análise estática PySpark/Delta). Nada aqui chama a Azure:
toda capability declarada é `LOCAL_READ` sobre artefato já em disco;
identidade Azure (Entra ID, managed identity, service principal) nunca
sai da fronteira de `collect` desta forge. Especialista ausente degrada
para o fallback nomeado `native-analysis` — nunca para execução simulada.

| Op | Uso |
|---|---|
| `discover` | resolve os especialistas declarados nesta máquina (PATH, metadata de pacote, manifests, probes governados) → estados `NOT_INSTALLED`/`DISCOVERED`/`VERIFIED`/`INCOMPATIBLE`/`UNTRUSTED`; `--provider`, `--no-probe`, `--root` |
| `plan <intent>` | roteamento determinístico do intent para uma capability declarada — nunca executa; `--authorize RISCO`, `--no-probe`, `--root` |
| `run <provider> <capability>` | executa uma capability declarada sob a fronteira governada (argv puro, env saneada de credenciais `AZURE_*`/`ARM_*`/`DATABRICKS_*`/proxies, timeout, caps de saída, gate de risco); valores: `--target`, `--runtime`, `--operation`, `--table-format`, `--check`, `--dialect`; `--authorize RISCO`, `--timeout`, `--no-persist`, `--root` |
| `handoffs` | lista os `EvidenceHandoff` persistidos em `.sparkforge-azure/delegation/handoffs/` (`--root`) |

Evidência sai como `theforge/EvidenceHandoff/v1` selado (SHA-256),
redigido e limitado; cada recusa carrega código nomeado
(`provider-absent`, `version-incompatible`, `capability-absent`,
`policy-refusal`, `cycle-detected`, `budget-exhausted`, `timeout`,
`runtime-error`, `invalid-output`, `insufficient-evidence`, …).
`--authorize` aceita `LOCAL_READ`, `LOCAL_WRITE`, `EXTERNAL_READ`,
`EXTERNAL_WRITE`, `DESTRUCTIVE`, `COST_BEARING`.

Evidência E2E do ciclo de integrações (casos A/B/E/G/H, mesma fronteira
delegation/ do sibling AWS): `forge-cli/docs/integration/cases/`.

## `sparkforge-azure evals <op>` — superfície §7.2 de avaliação

Inventário classificado das 9 suites de evals nas 4 categorias do §7.1
(developer, runtime-decision, output-verification, host-conformance).
Fonte: `sparkforge_azure/evals/taxonomy.py`; taxonomia em
`docs/evals-taxonomy.md`.

| op | efeito |
|---|---|
| `list` | `evals.list` — inventário classificado com contagens por categoria |
| `describe` | `evals.describe --suite <id>` — categoria, ambiente, selagem e sha256 de integridade; gabarito selado nunca sai |
| `run` | `evals.run --suite <id>` — runner determinístico da suite; suites de host recusam `EVALS-REQUIRES-HOST` |
| `result` | `evals.result --suite <id> --run <run>` — scorecard de uma execução de host gravada em `~/.sparkforge-azure/agentic-evals/` |

§7.4 (verification): `verification.plan` → `lab plan <cenario>`;
`verification.run` → `lab verify` (evidência de execução via
`lab run --execute --confirm` + `lab inspect`/`lab reproduce`).

## Exit codes

| Código | Significado |
|---|---|
| `0` | sucesso |
| `1` | findings emitidos ou resultado bloqueado |
| `2` | uso inválido / recusa de entrada |

## Verbos planejados (ainda não implementados)

`analyze <kind>` para kinds sem extrator e `knowledge check` aparecem como
`planned_tool_refs` em skills — são o contrato-alvo, não comandos
existentes hoje. A superfície atual é a listada acima (`sdd`, `agents`,
`agentops` e `mcp` já são implementados — ver as seções próprias).
