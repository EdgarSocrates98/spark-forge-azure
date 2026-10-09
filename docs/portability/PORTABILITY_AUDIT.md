# Portability Audit — Spark Forge Azure

Auditoria exigida por `prompt_evo_portable.md` §4–§7 **antes de qualquer código**.
Cobre os três repositórios lado a lado e classifica cada capability dos
referenciais em `COPY_SAFE` / `ADAPT` / `REFERENCE_ONLY` / `DO_NOT_PORT`.

## Baseline registrada

| Campo | Valor |
|---|---|
| `BASE_SHA` | `9f5a1f78251ac91ac94a676f33bc192ea4fb525a` (main pós-merge PR #21) |
| `PACKAGE_VERSION` | `0.1.0` (`pyproject.toml`) |
| `CLI_VERSION` | `sparkforge-azure 0.1.0` |
| `FREEZE_STATUS` | `frozen` — `tests/test_architecture_freeze.py` + `tests/test_architecture_layers.py`: 8 passed |
| Branch desta wave | `feat/portable-distribution` |
| Suite no BASE_SHA | 2919 passed, 9 skipped; claims 24/24 |

Referenciais auditados em disco: `E:\projetos\api-forge` (`src/apiforge`),
`E:\projetos\spark-forge-aws` (`sparkforge_aws`). Nenhum arquivo deles foi
modificado (§210 — reference only).

## 1. O que o API Forge tem (referencial primário de distribuição)

O único dos três com um ciclo de distribuição portátil completo:

- `apiforge/distribution/paths.py` — `resolve_paths()`: `package_root`,
  `executable`, `state_root` (`APIFORGE_HOME` ou `<projeto>/.apiforge`),
  `config_path` (`APIFORGE_CONFIG`), `cache_root` (`APIFORGE_CACHE`), com
  proveniência por campo (`sources: (name, PathSource)`). Relativos ancoram no
  cwd; overrides nunca escrevem.
- `apiforge/distribution/config.py` — `resolve_config()`: precedência
  `defaults → user config → workspace → project → CLI overrides`, recusa chave
  com cheiro de segredo (`AF-MANIFEST-SECRET`), YAML estrito.
- `apiforge/distribution/assets.py` — inventário de assets empacotados via
  `importlib.resources.files("apiforge.host_assets")` + sha256 por arquivo.
- `apiforge/distribution/doctor.py` — diagnose offline: state writável,
  `git`/MCP no PATH, rede declarada não-probada, assets presentes; status
  `ready|degraded|blocked`, gaps nomeados com `field`/`unlock`.
- `apiforge/application/portable.py` + `cli_distribution.py` — verbos
  `distribution inspect|init|status|doctor` sobre os serviços acima.
- `apiforge/workspace/` — `discovery.py` (caminhada de ancestrais limitada,
  sem varredura de home), `manifests.py` (`.apiforge/project.yaml` e
  `.apiforge/workspace.yaml`, YAML estrito + contratos pydantic),
  `service.py` (status/init/add/graph), `graph.py` (grafo declarado +
  inferência opt-in auditada), `locality.py` (`plan_locality`: tiers
  target/direct/transitive com `excluded` explícito e "deferred" como razão).
- `apiforge/host_assets/` — `manifest.yaml` + templates (`CLAUDE.md.tmpl`,
  `AGENTS.md.tmpl`, `mcp_config.json.tmpl`) carregados via
  `importlib.resources`, render `string.Template`, sha256 registrado.
- `apiforge/agentops/hosts.py` — tabela `HostAdapter` (claude, gpt-codex,
  devin, copilot) com `supports_mcp`/`supports_subagents`; `agentops hosts`,
  `agentops parity`, activation plan plan-only.
- `apiforge/forge/` — protocolo Forge (`discover_capabilities`, `submit_task`,
  `prepare_handoff`, …) para o Forger consumir capabilities públicas.
- `.devin/` nativo (`config.json`, `hooks.v1.json`, skills) + verbos
  `devin payload|probe|capabilities`.
- Não encontrado: `detach`. A saída portátil não existe no referencial —
  gap dele também, não só nosso.

## 2. O que o Spark Forge AWS tem (referencial de host install)

Sem camada `distribution`/`workspace` CLI, mas com a máquina de integração
de host mais completa dos três:

- `sparkforge_aws/integrate/hosts.py` — tabela declarativa por host com fonte
  documentada: `claude` (plugin marketplace dir `~/.sparkforge_aws/claude`),
  `devin` (`~/.config/devin` ou `%APPDATA%\devin`), `codex` (`~/.codex`,
  config TOML), `copilot` (`~/.copilot`). Nenhum caminho sai de env não
  injetado — `home`/`windows`/`appdata`/`codex_home` são parâmetros.
  `mcp_command`/`mcp_entry` geram a entrada `mcpServers` JSON/TOML.
- `sparkforge_aws/integrate/writer.py` — manifest de instalação com sha256 por
  arquivo escrito, `gravar_atomico`, `apply_json_config`/`apply_toml_config`
  com registro, `_editado` (drift: arquivo mexido depois do write),
  `revert_json_config`/`revert_toml_config` (rollback da config),
  `remove_owned` (remove só o que o manifest declara), `integrated_hosts`,
  `drop_manifest_if_empty`. É detach sem o nome.
- `sparkforge_aws/integrate/conflict.py` — detecção de conflito/ownership.
- `sparkforge_aws/integrate/render.py`, `claude.py`, `sources.py` —
  renderização multi-host (md/toml), plugin Claude marketplace.
- `sparkforge_aws/workspace/` — o mesmo pacote que o Azure já portou
  (manifest/graph/federated/semantic/freshness/impact).
- `paths.py`, `doctor.py`, `context/` gateway — já portados ao Azure.
- `playbook <coordinator>` — piso de dispatch sem subagents.
- Estado `~/.sparkforge_aws/`, `.sparkforge/` legado.

## 3. O que o Spark Forge Azure já tem (estado real em BASE_SHA)

Reusável diretamente — **não duplicar** (§228):

| Peça | Local | Estado |
|---|---|---|
| Confinamento de path | `paths.py` (`resolve_within`, `scan_repository`, `WorkspaceScanPolicy`) | pronto |
| State dir | `paths.py:state_dir()` → `<cwd>/.sparkforge-azure` ou `SPARKFORGE_AZURE_STATE_DIR` | pronto, respeita §101 |
| Assets no wheel | `pyproject.toml` force-include → `sparkforge_azure/_data/{rules/catalog,knowledge,skills,agents,lab/scenarios}`; `doctor.py:data_root()` alterna source↔wheel | pronto (§143 meio caminho) |
| Doctor | `doctor.py` + `sparkforge-azure doctor [--area]` (check único, offline, `ok/warn/fail/unresolved`) | existe, não é `distribution doctor` |
| Workspace manifest (grafo) | `graph/workspace.py` — `sparkforge-azure.workspace.yaml` commitável: repositories com `role` + path relativo **contido na root**, `relationships`, `bindings`, `cloud_resources`, `domains`, `boundaries` | domínio grafo/cloud, não ForgeWorkspace |
| Workspace manifest (federação) | `workspace/manifest.py` — loader próprio (`relationships` em **dict**, schema distinto) usado por `workspace/federation.py` | **segundo schema** — não criar terceiro |
| Context gateway | `context/` (`gateway`, `planner`, `funnel`, perfis economy/balanced/deep, `ContextPack`) | pronto; falta resolução por workspace/target |
| TokenSave | `tokensave/engine.py` + `tokensave context` | pronto |
| CodeIntel | `codeintel/` (`indexar(raiz, banco)` sqlite, `root_fingerprint`, incremental) | pronto; index chaveado por path hoje |
| Agent mirrors | `agentmanifest/mirrors.py` → `.claude/agents/custom`, `.agents/agents` (prefixo `sparkforge-azure-`, tools read-only + Bash condicional) | pronto |
| MCP | `mcp serve` stdio/http + `mcp catalog` | pronto |
| CLI | `cli/main.py` — `COMMAND_MODULES` fechado, 1 JSON/comando, exit 0/1/2, surface lock | pronto |
| Identidade de frota | `agentic/fingerprint.py` (sha256 do contrato — não é project_id) | ortogonal |

## 4. Gaps reais do Azure (o que o spec pede e não existe)

1. **Sem `distribution` command group** — `inspect|init|status|doctor|detach`
   não existem. `doctor` isolado cobre instalação, não o lifecycle portátil.
2. **Sem `workspace` command group** — `discover|init|add|remove|status`
   não existem; manifests são escritos à mão.
3. **Contenção obrigatória** — `graph/workspace.py:_safe_repo_path` recusa
   caminho absoluto/`..`: `workspace add ../shared-lib` (fluxo §216) é
   impossível no schema do grafo. Correto para o grafo (boundary de
   autorização), mas o ForgeWorkspace precisa de repos externos declarados.
4. **Dois schemas de workspace coexistem** (`graph/workspace.py` lista-de-
   relationships vs `workspace/manifest.py` dict-de-relationships). O novo
   manifest não pode ser um terceiro esquema concorrente: nasce como
   artefato da camada de distribuição em `.sparkforge-azure/workspace.yaml`
   (estado local, já gitignored), nome e local distintos dos dois existentes.
5. **Sem `project_id` estável** — nenhuma identidade lógica separada do path.
6. **Sem `context resolve`** — o gateway recebe task string; não resolve
   workspace→target→deps→locality.
7. **Sem geração de host config** — mirrors existem mas MCP config/host
   detection/managed markers não existem.
8. **Sem detach** — nada remove assets managed.
9. **Sem receipts de distribuição**, drift states, ou `check_portability.py`.
10. **Cache dir** — não há `SPARKFORGE_AZURE_CACHE` equivalente (só state dir).

## 5. Matriz de paridade (§7, §137–§139)

Estados: `EQUIVALENT` · `AZURE_AHEAD` · `REFERENCE_AHEAD` · `DIFFERENT_BY_DESIGN`.

| Capability | API Forge | Spark Forge AWS | Spark Forge Azure | Gap | Portability class | Action |
|---|---|---|---|---|---|---|
| Env path overrides w/ provenance | `resolve_paths` + `sources` | parcial (`integrate/hosts.py`) | `state_dir()` só | state/cache/config sem proveniência única | ADAPT | `distribution/paths.py` sobre `paths.py` |
| Config precedence + strict | `resolve_config` 5 níveis + `AF-MANIFEST-SECRET` | — | — | ausente | ADAPT | `distribution/config.py` dataclass/yaml (sem pydantic) |
| Packaged asset inventory+sha256 | `distribution/assets.py` | — | `data_root()` resolve, sem inventário | inventário/hash ausente | ADAPT | `distribution/assets.py` via `importlib.resources` |
| Offline distribution doctor | `distribution/doctor.py` | `integrate` health | `doctor.py` | não cobre lifecycle portátil | ADAPT | `distribution doctor` compõe `doctor.run` + checks novos |
| `distribution init/inspect/status` | `application/portable.py` | — | — | ausente | ADAPT | `distribution/service.py` |
| Workspace manifest + service | `workspace/{manifests,service}.py` | `workspace/` (portado) | dois schemas de grafo | schema ForgeWorkspace ausente | ADAPT | `.sparkforge-azure/workspace.yaml` novo, nome/local distintos |
| Bounded discovery | `workspace/discovery.py` ancestrais | — | — | ausente | ADAPT | `distribution/discovery.py` bounded |
| Locality tiers target/direct/transitive | `workspace/locality.py` | — | — | ausente | ADAPT | dentro de `context resolve` |
| Repo fora da root declarado | `RepositoryRef` (abs root) | — | recusado por `_safe_repo_path` | bloqueado no schema grafo | ADAPT | ForgeWorkspace permite; grafo mantém contenção |
| `project_id` ≠ path | `sha256(abs path)` | — | — | API Forge **viola** §39 | DO_NOT_PORT | id gerado (uuid4), persistido; path é `location` |
| Copy collision detection | — | — | — | ausente nos três | ADAPT | registry de ids conhecidos + `identity_collision` |
| Host adapter table | `agentops/hosts.py` (4 hosts) | `integrate/hosts.py` (4 hosts, paths sourced) | mirrors só | tabela+paths ausente | ADAPT | `distribution/hosts.py` (claude/devin/codex + mcp) |
| Install manifest + drift + revert | — | `integrate/writer.py` (1020 LoC) | — | ausente | ADAPT | `distribution/managed.py` mínimo (receipt+sha256+drift) |
| Managed markers em config | — | `writer.py` blocos TOML + `_limites_do_bloco` | — | ausente | ADAPT | markers `BEGIN/END sparkforge-azure` |
| Detach/reattach | — | `writer.remove_owned` (biblioteca) | — | ausente | ADAPT | `distribution detach` sobre `managed.py` |
| Claude marketplace plugin | — | `integrate/claude.py` | — | fora de escopo | REFERENCE_ONLY | pipx + `.mcp.json` de projeto bastam |
| `.devin/` hooks nativos | `.devin/` completo | — | — | fora de escopo | REFERENCE_ONLY | mirrors `.agents/` já cobrem Devin |
| Forge wire protocol | `forge/protocol.py` (7 ops) | — | — | desnecessário | REFERENCE_ONLY | Forger lê `distribution inspect`+manifest |
| Segundo schema `workspace/manifest.py` | — | legado portado | existe | risco de 3º schema | DO_NOT_PORT | não reusar; deprecar em follow-up se virar dead code |
| LLM/AI para discovery | nenhum | nenhum | nenhum | n/a | DO_NOT_PORT | §214/§215 proíbem |

## 6. Decisões de arquitetura derivadas do audit

1. **`sparkforge_azure/distribution/`** — pacote novo, camada de produto
   (não domínio Azure). Importa `paths`, `agentmanifest`, `skills`,
   `doctor` (leitura), e nada de `azure`/`collectors`/`context` (o resolve
   mora na W4 em `context/` ou módulo próprio consumindo o manifest).
   Arestas novas serão declaradas em `EXCECOES_MEDIDAS` com razão.
2. **Dois conceitos de workspace, nomes distintos** —
   `sparkforge-azure.workspace.yaml` (commitável, boundary de autorização do
   grafo, contenção obrigatória) permanece intocado; o ForgeWorkspace vive em
   `.sparkforge-azure/workspace.yaml` (estado local por máquina). Sem schema
   novo concorrente com `workspace/manifest.py` — que fica isolado ao seu
   consumidor (`federation.py`).
3. **`distribution init`** escreve `.sparkforge-azure/project.yaml`
   (identity + proveniência) e `.sparkforge-azure/receipt-distribution.json`
   (managed files + sha256 + package version + host configs). Idempotente:
   re-run = mesmo id, receipt atualizado, nenhum arquivo do usuário tocado.
4. **Identity** — `project_id = "sfa-" + uuid4().hex[:24]` gerado uma vez e
   persistido; nunca derivado de path (§39). `workspace_id` idem. Colisão de
   cópia: `identity_collision` estruturado, sem merge silencioso.
5. **Config precedence** — `CLI > project > workspace > user > defaults`,
   inspecionável via `inspect` (value+source por campo), chaves desconhecidas
   = `manifest_invalid`/named unresolved (§47), chaves com cheiro de segredo
   recusadas (§119).
6. **Cache** — `SPARKFORGE_AZURE_CACHE` novo override alinhado a state dir
   (§102); default `<state>/cache`.
7. **Host integration mínima** — project-scope: `.mcp.json` (claude/devin
   style) + markers managed; `mcpServers.sparkforge-azure` aponta o binário
   `sparkforge-azure mcp serve` instalado, nunca path de checkout (§75).
   Detecção via `shutil.which` + dirs conhecidos; ausente = `unavailable`,
   nunca erro (§76–77).
8. **Detach** — `distribution detach [--dry-run] [--purge-state]`:
   remove só o que o receipt declara (managed files, blocos marked), preserva
   estado/cache por default; reattach = `init` idempotente.
9. **Sem `distribution repair`** — `init` idempotente cobre (§113).
10. **Erros** — failure kinds do §178 como `error.kind` estruturado no JSON;
    nunca traceback cru (§179).
11. **Arestas de arquitetura previstas** (a declarar): `cli→distribution`,
    `cli→workspace`(existente), `distribution→paths`, `distribution→agentmanifest`,
    `distribution→skills`, `distribution→doctor`, `context→distribution` (W4),
    `cli→context` (já existe? verificar — `cmd_tokensave` usa tokensave;
    `context resolve` criará `cli→context` se `context` ganhar verbo novo).

## 7. Open questions (não inventar — registrar)

- OQ-1: `workspace remove` — spec diz "avaliar, provavelmente sim" (§149).
  Implementado: remove só declaração, nunca o repo (§150).
- OQ-2: `.devin/` mirror dedicado — Devin já lê `.agents/`; sem prova de
  necessidade, não criar (DO_NOT_PORT até evidência).
- OQ-3: Forge wire protocol — `distribution inspect` JSON + manifest é a
  superfície pública; protocolo novo só se um consumidor real pedir.

## 8. Escopo final desta wave

W1 `distribution/` (paths/config/assets/model/service/inspect/cli,
init/inspect/status/doctor) → W2 `workspace` (discover/init/add/remove/status,
manifest, roles, deps, ciclos) → W3 identity relocável → W4 `context resolve`
→ W5 host integration → W6 detach → W7 provas T0–T4, gate, claims, docs×8,
SDD×6. Cada onda commitada separadamente; freeze re-verificado ao final.
