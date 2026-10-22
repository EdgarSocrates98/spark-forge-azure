# FORGE_CONTEXT_BASELINE — spark-forge-azure

Auditoria do Ciclo 1 (lf-0034 / `prompt_evo_install2.0.md` §3). Documento de
evidência: cada afirmação cita o comando executado ou o arquivo:linha
inspecionado. Nada aqui foi preenchido por suposição.

- Repo: `/home/edgar/Documentos/projetos/forjas/spark-forge-azure`
- SHA: `d35305c2b6eacfb35d6d9c38061894e680f04330` (`git rev-parse HEAD`, branch `main`, worktree limpo)
- Versão declarada: `0.1.6` (`pyproject.toml`, `sparkforge_azure/__init__.py`)
- Python requerido: `>=3.10`
- Data da auditoria: 2026-10-22
- Referência madura comparada: `data-sentinel-forge@92f245f` (installkit com
  `install manifest`, `install env`, `install mcp-verify`, `MANIFEST.sha256`
  de assets, 5 hosts incl. `cursor`, wizard interativo via typer)

---

## 1. Inspeção de arquitetura (§3.1)

### 1.1 Módulos

`sparkforge_azure/` contém subpacotes `agentic`, `agentmanifest`, `cli`,
`context`, `distribution`, `doctor.py`, `economy`, `evals`, `graph`,
`install`, `knowledge`, `mcp`, `paths.py`, `portal`, `tokensave`, `workspace`
(enumerados via `ls sparkforge_azure/`; a superfície exata de módulos é
travada por `scripts/check_surface_lock.py` + `docs/surface.lock.json`).

Arquivos vendored (canônico fora deste repo — **não editar aqui**):

| Arquivo | Canônico declarado | Evidência |
|---|---|---|
| `sparkforge_azure/_installkit.py` | `the-forge/scripts/installkit/forge_installkit.py` | docstring linhas 3-6; `_INSTALLKIT_VERSION = "1.0.0"`, `_SOURCE_SHA256 = "bc189dd2ae0028ce"`; sha256 `37250539…` **byte-idêntico** aos de `sparkforge_aws` e `data_sentinel` (`sha256sum` dos três) |
| `sparkforge_azure/_graphview.py`, `_graphstudio.py`, `_forge_portal.py`, `_portal_telemetry.py`, `ui/` | `the-forge` / `forge-portal` | mesma convenção de vendor do AWS (`_SOURCE_SHA256` + ignores do ruff) |
| `scripts/forge_bootstrap.py`, `install.sh` | `the-forge` | sha256 `c9d1d583…` / `2cb7764c…` idênticos ao AWS (`diff -q` sem diferença) |

### 1.2 CLI

- Entry point (`pyproject.toml`): `sparkforge-azure` →
  `sparkforge_azure.cli.main:main`. Contrato de nome (`AGENTS.md` invariante 1):
  CLI `sparkforge-azure`, pacote `sparkforge_azure`, env `SPARKFORGE_AZURE_*`,
  estado `.sparkforge-azure/`, tools `sfa_*` — nunca `sparkforge` genérico.
- 26 verbos de topo (`sparkforge-azure --help`, venv limpo):
  `version, ai, tokensave, governance, doctor, graph, collect,
  offline-bundle, lab, mcp, diagnose, migration, sdd, agents, agentops,
  analyze, judge, knowledge, distribution, install, portal, workspace,
  context, delegate`.
- `install` (forge/* install lifecycle):
  `apply/status/doctor/repair/uninstall/update/mcp-verify`.
- `distribution` (portable distribution lifecycle):
  `inspect/init/status/doctor/detach`.
- `agents`: `list/inspect/route/fingerprint/impact/runtimes/
  runtime-inspect/execute/compare` (fleet contract surface).
- **Ausente**: `install manifest` e `install env` — os verbos que o
  data-sentinel expõe (`src/data_sentinel/cli/install.py:228,252`).
  `forge.json`/`forge.agentic.json` não são emitidos por nenhum verbo.
- UTF-8 stdio fix presente: `sparkforge_azure/cli/main.py` reconfigura
  stdout/stderr UTF-8 (`_stdio_utf8`) — mesmo fix que o sentinel faz em
  `cli/__init__.py._configure_stdio()`; Azure já cobre este ponto do baseline.

### 1.3 Installkit e instalação portátil

- `_installkit.py` vendored (v1.0.0, idêntico aos siblings) — schemas
  `forge/InstallationManifest/v1`, `InstallReceipt/v1`, `InstallationHealth/v1`,
  `WorkspaceInstall/v1`; ledger sha256; merge de `.mcp.json`; marker blocks;
  registry `~/.forge/installations/` (observado nesta máquina:
  `spark-forge-azure.json` presente junto a 6 outros forges).
- `sparkforge_azure/install/service.py` + `cli/cmd_install.py`: ciclo de vida
  `apply/status/doctor/repair/uninstall/update` + `mcp-verify`.
- `sparkforge_azure/distribution/`: `service.py` (`initialize()`, ledger,
  receipts), `assets.py` (resolução source/wheel), `hosts.py` (tabela de
  hosts), `managed.py` (arquivos gerenciados + ledger), `detach.py`,
  `hostfiles.py` (marker `<!-- sparkforge-azure:begin -->`).
- `sparkforge_azure/paths.py`: `PKG`, `REPO`, `data_root(kind)`,
  `fleet_root()`, `state_dir()` — resolução única: source → raiz do repo;
  wheel → `sparkforge_azure/_data/`; nunca cwd do caller.
- `sparkforge_azure/agentmanifest/mirrors.py` + `scripts/sync_skill_mirrors.py`:
  renderização dos mirrors de host a partir de `agents/` e `skills/` canônicos.

### 1.4 Integração com hosts

- Alvo de projeto: `.sparkforge-azure/` (ledger + `project.yaml` identidade +
  receipts), `.mcp.json` com `mcpServers.sparkforge-azure`, marker blocks em
  `AGENTS.md`/`CLAUDE.md` (observado injetado — bloco citado no §3).
- `.mcp.json` escrito usa `command: "sparkforge-azure"`, `args: ["mcp",
  "serve"]` — resolvido por PATH do host (diferente do AWS, que grava o
  `sys.executable` absoluto; ver GAP-P1).
- `distribution/hosts.py`: tabela declara **3 hosts** (claude, devin, codex);
  mas o parser de `install` aceita `--host claude|devin|codex|copilot|all`
  (`cmd_install.py`) → assimetria CLI vs tabela (GAP-P2).
- Escopo `user` usa `~/.sparkforge-azure` de estado.

### 1.5 MCP adapters

- `sparkforge_azure mcp catalog` → catálogo JSON offline; `mcp serve` →
  stdio ou streamable http.
- `doctor` reporta `mcp | ok | 18 tools, all with declared risk` (venv limpo,
  evidência §4) — superfície `sfa_*` bem menor que os 148 tools do AWS
  (assimetria de capacidade MCP entre os dois forges, fato, não defeito).
- `install mcp-verify`: handshake spawnando `sparkforge-azure mcp serve` —
  **resolvido por PATH**, não pelo interpretador que reporta (ver risco §5).

### 1.6 Empacotamento

- `pyproject.toml`: hatchling, builds reproduzíveis declarados; extras
  `azure`, `databricks`, `mcp`, `otel`, `dev`; dependências `PyYAML>=6.0`,
  `jsonschema>=4.0`.
- Wheel `force-include`: `rules/catalog` → `sparkforge_azure/_data/rules/
  catalog`, `knowledge` → `_data/knowledge`, `skills` → `_data/skills`,
  `agents` → `_data/agents`, `lab/scenarios` → `_data/lab/scenarios`,
  `evals` → `_data/evals`, `portal/assets` → `portal_assets`.
- Inventário medido do wheel (venv limpo, `distribution inspect` + enumeração
  de `_data/`): **256 assets** — skills 47 arquivos, agents 42, knowledge 49,
  rules 11, evals 105, lab 2.

### 1.7 Schemas, manifests, assets

- `forge.json` (raiz): `forge_id spark-forge-azure`, package/distribution/cli,
  `python >=3.10`, `mcp_server_name`, `mcp_command`, `extras:[mcp]`, `lab`
  (command/receipt/modes/suite/timeout). **Sem `version` e sem
  `install_command`** — o sentinel tem ambos (`install_command:
  "data-sentinel install --yes"`).
- `forge.agentic.json` (raiz): `forge/SpecialistAgenticManifest/v1`,
  `version "0.1.0"` **defasada** vs pacote 0.1.6; workflows `analyze`,
  `doctor`; **`skills: []`, `agents: []`, `coordinators: []` — vazios**
  apesar de 23 skills + 40 agents canônicos existirem. `host_adapters`:
  [claude, devin, codex, copilot]; `requires_network: false`.
- `manifest.json` (raiz): capability statuses (supported/planned) — fonte de
  verdade de status junto a `parity.yaml`.
- `.mcp.json` (raiz): declara `sparkforge-azure` para o checkout.
- Assets fonte: `skills/` 23 skills (`*/SKILL.md`), `agents/` 40 `.md` +
  `CAPABILITY.json` (gerado por `scripts/gen_agent_capability.py`),
  `knowledge/` 49 arquivos, `rules/catalog/` 10-11 yamls, `evals/` 109
  (incl. `host_proof/claude_code.json` — prova real de spawn com tokens
  medidos), `lab/scenarios/` 2.
- Locks de superfície: `docs/surface.lock.json`, `docs/claims.lock.json` —
  presentes no checkout, **não entram no wheel** (`doctor` →
  `surface: unresolved "surface lock not present in this build"`,
  `claims: unresolved idem` — evidência §4).

### 1.8 Canônico vs gerado

| Recurso | Canônico | Gerado | Gerador oficial |
|---|---|---|---|
| Skills | `skills/*/SKILL.md` (23) | `.claude/skills` (23), `.agents/skills` (23) | `scripts/sync_skill_mirrors.py` + `agentmanifest/mirrors.py` |
| Agents | `agents/*.md` (40, front matter v2) | `.agents/agents` (40), `.claude/agents/custom` (40) | `agentmanifest/mirrors.py` |
| Fleet inventory | `agents/*.md` | `agents/CAPABILITY.json` | `scripts/gen_agent_capability.py` |
| `.mcp.json` do alvo | — | escrito pelo install | `distribution/hostfiles.py` |
| Marker `AGENTS.md` | — | bloco gerenciado | `distribution/hostfiles.py` |

Observação: os agentes instalados carregam o manifesto v2 completo
(`schema_version, id, kind, family, domain, role, mission, does, does_not,
inputs, outputs, allowed_tools, denied_tools`) como `.md` gerado — verificado
lendo um `.claude/agents/custom/sparkforge-azure-*.md` no alvo.

### 1.9 Docs de instalação, testes, CI/CD, PyPI

- `docs/` com índice (`docs/README.md`, gate `check_docs_index.py`),
  `docs/product/PRODUCT_DEFINITION.md`, `docs/sdd/`,
  `docs/architecture/{adr,evidence/provenance.json}`,
  `AWS_TO_AZURE_PORTABILITY_MATRIX.md`, `parity.yaml`.
- Gates de repo (`AGENTS.md`): ruff, pytest, `check_surface_lock.py`,
  `check_docs_surface.py`, `check_docs_index.py`, `check_portability.py`,
  `check_claims.py`.
- Porting do AWS é travado: `scripts/port_from_aws.py` +
  `scripts/port_manifest.yaml` + `provenance.json` (hash por arquivo
  `COPY_SAFE`).
- PyPI: `sparkforge-azure==0.1.6` publicado. Local vs PyPI
  (`pip download` + `sha256sum`):
  wheel `3b791bffbf6a9f70a6c1e8dca7d9716caa553aa12d01637641deb4dc56bcd203`
  **idêntico**; sdist `97f68234af16bed672334af8b16167855fd0d01d78a1f55e83af
  2af2af5416da352` **idêntico** — build reproduzível bit a bit.

---

## 2. Matriz de recursos (§3.2)

Só evidência executada. ✅ direto · ⚠️ parcial/condicional · ❌ ausência/falha
evidenciada · `n/a`.

| Recurso | Existe na fonte | Está no wheel | Instalado no alvo | Descoberto pelo host | Utilizável | Verificado |
|---|---|---|---|---|---|---|
| Skills | ✅ 23 `*/SKILL.md` (`find skills -name SKILL.md`) | ✅ `_data/skills` 47 arquivos (inventário do wheel) | ✅ `.claude/skills` 23 + `.agents/skills` 23 no alvo (install full → 177 managed) | ✅ layout nativo claude/devin | ⚠️ mirrors carregam `knowledge_refs` repo-relativos (mesma classe de quebra do AWS, ver GAP-P0-2) | ⚠️ suites de eval empacotadas; nenhuma prova de host carregando skill |
| Agents | ✅ 40 `.md` + `CAPABILITY.json` | ✅ `_data/agents` 42 arquivos | ✅ `.agents/agents` 40 + `.claude/agents/custom` 40 (nomes `sparkforge-azure-*.md`) | ⚠️ `.agents/agents` nativo p/ Devin; `.claude/agents/custom` subdir (verificar se Claude varre `custom/` — layout não padrão) | ⚠️ `doctor.agentic_fleet` marca todos como `broken` no wheel (GAP-P0-1) | ⚠️ `agents list` → `unevaluated` (fleet resolve via `fleet_root()`); `evals/host_proof` tem prova real de spawn p/ 1 agente |
| MCP | ✅ `mcp catalog`/`serve`, 18 `sfa_*` | ✅ módulo no pacote | ✅ `.mcp.json` com chave `sparkforge-azure` | ✅ `.mcp.json` de projeto | ⚠️ exige extra `[mcp]`; comando resolvido por PATH (pode servir binário de outra instalação) | ⚠️ `install mcp-verify` existe — mas spawn PATH-based não prova o venv que reportou (ver §4.5) |
| Knowledge | ✅ 49 arquivos | ✅ `_data/knowledge` 49 | ❌ não copiado (REFERENCIAR no pacote) | ❌ sem índice/manifesto p/ host | ⚠️ `knowledge select` existe; **não há `knowledge path`** (0.1.6 expõe só `select`) | ⚠️ `doctor.knowledge_freshness` → 37 entries ok |
| Rules | ✅ `rules/catalog` ~10-11 yamls | ✅ `_data/rules/catalog` 11 | ❌ não copiado | ❌ | ⚠️ `judge` aplica catálogo do pacote | ⚠️ via CLI apenas |
| Evals | ✅ `evals/` 109 (incl. `host_proof/`) | ✅ `_data/evals` 105 | ❌ não copiado | ❌ | ⚠️ `sparkforge-azure evals`/lab roda suítes | ⚠️ `host_proof/claude_code.json` é prova real pré-existente (runtime claude_code, tokens medidos) |
| Protocols | ✅ `AGENTS.md` raiz (contrato de repo) | ❌ fora do wheel | ⚠️ marker block injetado no `AGENTS.md` do alvo (evidência: bloco `<!-- sparkforge-azure:begin -->` visto injetado) | ⚠️ marker descoberto pelo host, mas **texto aponta verbos obsoletos** (`distribution status|doctor|detach`, `distribution init --with-mirrors` — `hostfiles.py:43-44`) | ⚠️ marker existe; orientação parcialmente errada | ⚠️ |
| Verificadores | ✅ `scripts/check_*.py` (surface, docs, portability, claims, knowledge) | ❌ `scripts/` fora do wheel | ❌ | ❌ | ⚠️ `sdd check`/`doctor` embutidos | ❌ `doctor` reporta `surface`/`claims` `unresolved` porque os locks não viajam no pacote |
| Políticas | ✅ `governance` verb, AGENTS.md invariantes, `denied_tools` nos manifests | ⚠️ módulos de política no pacote | ❌ hooks/permissions do repo não vão ao alvo | ❌ | ⚠️ `allowed_tools`/`denied_tools` copiados nos mirrors de agente | ⚠️ |

---

## 3. Análise do instalador (§3.3)

Código: `sparkforge_azure/install/service.py`, `cli/cmd_install.py`,
`distribution/{service,assets,hosts,managed,detach,hostfiles}.py`,
`paths.py`, `_installkit.py`.

### Resolução do alvo

- `install apply` resolve alvo por escopo (project/workspace/user) via
  installkit; `--root` explícito ou raiz VCS/workspace; `user` →
  `Path.home()`/`~/.sparkforge-azure`.
- `paths.py`: dados do pacote resolvem por `data_root()` — source → raiz do
  repo; wheel → `sparkforge_azure/_data`; o cwd do caller **nunca** é usado
  para frota (`fleet_root()`), confirmado por `distribution inspect` no venv:
  `"source": "wheel"`, `asset_count: 256`, `portable_distribution: true`,
  `context_resolution: true`, `detach_safe: true`, `forge_workspace: true`.
- `distribution/service.initialize()` cria/mantém `project.yaml`
  (identidade), `.mcp.json`, markers, mirrors opt-in, receipts + ledger.

### Scopes e perfis

- Escopos `project`, `workspace`, `user` (mesmo trio do AWS/installkit).
- `--profile minimal|recommended|full`: minimal = markers + chave MCP;
  recommended = + skill mirrors; full = + agent mirrors. Observado:
  `install apply --profile full` → `completed`, **177 managed entries**
  (vs ~1 498 do AWS — footprint muito menor porque Azure copia só o
  `.md`/`SKILL.md` do espelho, não a árvore inteira de references/scripts).
- `--gateway-profile economy|balanced|deep`: mesma família do AWS.
- Hosts: `--host claude|devin|codex|copilot|all` no parser — mas
  `distribution/hosts.py` só declara claude/devin/codex; `--host
  claude,devin` rejeitado pelo argparse (executado; csv não é aceito).

### Merge, ownership, uninstall, repair, update

- `.mcp.json`: merge de chave `mcpServers.sparkforge-azure`, preserva outras
  chaves (installkit `apply_json_config`).
- Marker: `<!-- sparkforge-azure:begin/end -->` — conteúdo injetado observado
  no alvo (o próprio host leu o bloco: ver evidência em §2 Protocols).
  **Texto do marker está obsoleto**: diz `distribution status|doctor|detach`
  e `distribution init --with-mirrors` (`hostfiles.py:43-44`) — o ciclo de
  vida canônico agora é `install status|doctor|repair|uninstall` (GAP-P2).
- Ledger `.sparkforge-azure/` com ownership por arquivo; `detach`/uninstall
  só remove o que o ledger declara. Observado: `install uninstall` →
  `completed`, 97 removidos, 0 mantidos, sobra só estrutura de diretórios.
- `repair`/`update` existem na superfície (`install repair`,
  `install update`); update usa o registry `~/.forge/installations/
  spark-forge-azure.json` (mesmo fluxo do AWS: pip --upgrade do checkout
  registrado).
- Aprovação: `--yes`/dry-run presentes (installkit comum).

---

## 4. Diagnóstico PyPI (§3.4)

### 4.1 Build e artefatos

```
cd spark-forge-azure && python -m build --outdir /tmp/audit_azure/dist .
→ sparkforge_azure-0.1.6-py3-none-any.whl + sparkforge_azure-0.1.6.tar.gz
pip download sparkforge-azure==0.1.6 --no-deps -d /tmp/audit_azure/pypi
sha256 local  wheel = 3b791bff…bcd203 = PyPI wheel  (idêntico)
sha256 local  sdist = 97f68234…a352   = PyPI sdist  (idêntico)
```

`unzip -l` do wheel confirma `_data/` com 256 assets (47 skills / 42 agents /
49 knowledge / 11 rules / 105 evals / 2 lab), `portal_assets`,
`_installkit.py`, `_graphview.py`, `_graphstudio.py`, `_forge_portal.py`,
`ui/`. `forge.json`, `forge.agentic.json`, `manifest.json`, `AGENTS.md`,
`docs/surface.lock.json`, `docs/claims.lock.json`, `scripts/`, `tests/`:
0 ocorrências no wheel (grep na listagem).

### 4.2 Venv limpo fora do checkout

```
python3 -m venv /tmp/audit_azure/venv
venv/bin/pip install /tmp/audit_azure/dist/sparkforge_azure-0.1.6-py3-none-any.whl
cd /tmp/audit_azure/proj        # fora do checkout
venv/bin/sparkforge-azure --version → sparkforge-azure 0.1.6
```

### 4.3 `doctor` no wheel — evidência do P0

`sparkforge-azure doctor` → `status: fail`, summary `{ok:14, fail:1,
unresolved:7}`:

| check | status | detalhe |
|---|---|---|
| installation | ok | package_path → `/tmp/audit_azure/venv/lib/python3.12/site-packages/sparkforge_azure` |
| dependencies | ok | PyYAML, jsonschema |
| agentic_os | ok | 8 modules importable |
| **agentic_fleet** | **fail** | `broken agents: ['coordinator','inventory','extractor','analyzer','judge','verifier','reviewer','critic','referee',…]` — todos os 40 |
| tokensave | ok | retrieval ladder L0-L6 |
| graphfy / code_intelligence | ok | |
| agent_runtime | ok | 6 runtimes — adapter_implemented=6 **host_proven=0** |
| knowledge_freshness | ok | 37 knowledge entries (declared) |
| **mcp** | **ok** | 18 tools, all with declared risk |
| skills_agents | ok | **23 skills, 40 agents** ← contradiz agentic_fleet |
| surface | unresolved | "surface lock not present in this build" |
| claims | unresolved | "claims lock not present in this build" |
| access/fabric/streaming/migration_vertical | unresolved | "no source-tree fixtures (packaged install?)" — honesto |

**Causa-raiz** (`sparkforge_azure/doctor.py:448`): `_agentic_fleet()` chama
`inventory(REPO)`; `REPO = Path(PKG).parent` → em site-packages aponta para
`lib/python3.12/site-packages`, onde não existe `agents/`. O check ao lado,
`_skills_agents()` (linha 170), usa `data_root("agents")` e conta corretamente.
Prova direta (venv, mesma sessão):

```python
inventory(REPO)          → {'broken': 40, 'ready': 0, 'unevaluated': 0, …}
inventory(fleet_root())  → {'broken': 0, 'ready': 0, 'unevaluated': 40, …}
```

O fleet resolve bem — o bug é **só a raiz passada pelo doctor**.
`sparkforge-azure agents list` no mesmo venv reporta `status: unevaluated`
para todos os 40 — correto e consistente com `fleet_root()`. Ou seja: a falha
é de *reporte* (doctor mente `broken`), não de *conteúdo* (assets resolvem).

### 4.4 Install e ciclo de vida (venv limpo)

```
venv/bin/sparkforge-azure install apply --root /tmp/audit_azure/proj \
    --profile full --host all --yes
→ completed, 177 managed entries
venv/bin/sparkforge-azure distribution inspect --root .
→ source=wheel, asset_count=256, portable_distribution/context_resolution/
  detach_safe/forge_workspace = true
venv/bin/sparkforge-azure install uninstall --root . --yes
→ completed, 97 removed, 0 kept
```

`.mcp.json` do alvo: `{"mcpServers":{"sparkforge-azure":{"command":
"sparkforge-azure","args":["mcp","serve"]}}}`.

### 4.5 MCP verify — ressalva de evidência

`install mcp-verify` spawna `sparkforge-azure mcp serve` **por PATH**. Nesta
máquina existe um `sparkforge-azure` de sistema (bootstrap de `~/.forge`),
logo um PASS do verify pode provar o binário errado (PATH ≠ o venv que rodou
o verify). O `mcp_command` do `forge.json` e o `.mcp.json` gravado têm o mesmo
comportamento — consistente com `forge/SpecialistAgenticManifest`, mas menos
determinístico que o `sys.executable` absoluto que o AWS grava. Registrar
como risco de evidência, não como falha.

### 4.6 Outras verificações no venv

- `tokensave`, `graph`, `analyze` importam e respondem.
- `knowledge --help` → só `select` (sem `path`: conhecimento empacotado não é
  localizável por caminho — só por seleção semântica).
- `mcp catalog` → 18 tools `sfa_*` com risco declarado.
- `agents list` → 40 agents `unevaluated` (sem evals de fonte no pacote —
  `CAPABILITY.json` diz `ready` no checkout porque `tests/` existem lá).
- `install apply --host claude,devin` → rejeitado pelo parser (csv não
  aceito; mesmo comportamento do AWS).

---

## 5. Gaps P0 / P1 / P2

### P0

**GAP-P0-1 — `doctor.agentic_fleet` marca os 40 agents como `broken` numa
instalação de wheel válida.**
Causa-raiz: `doctor.py:448` — `inventory(REPO)` recebe a raiz errada
(`site-packages/` em vez de `sparkforge_azure/_data`); `inventory()` espera
um root com `agents/<id>.md`. O vizinho `_skills_agents()` (linha 170) usa
`data_root("agents")` corretamente; `agents list` usa `fleet_root()`
corretamente — três caminhos, um errado.
Risco: o único verbo de saúde que um operador roda numa instalação PyPI
declara a frota inteira quebrada — falso negativo sistêmico que mascara
qualquer regressão real e ensina o usuário a ignorar `doctor`. Também
envenena o `status: fail` do doctor inteiro.
Decisão proposta: `inventory(data_root())` (ou `fleet_root()`), com teste que
roda `doctor` num venv de wheel (não `pip install -e .`) e exige 0 broken.
Migração: corrigir a resolução + teste e2e; o estado "unevaluated" correto já
está implementado.

**GAP-P0-2 — referências `knowledge_refs`/`tool_refs` nos mirrors instalados
são repo-relativas → inalcançáveis no alvo.**
Causa-raiz: skills/agents gerados carregam `knowledge_refs` apontando para
caminhos do checkout; `knowledge/` fica dentro do pacote e não há verb
`knowledge path` (só `select`). Mesma classe do GAP-P0-2 do AWS (item 9 do
§1 do prompt: recursos existem mas o host não os alcança).
Decisão proposta: render do mirror troca refs por instruções de verb/MCP
(`knowledge select`, `sfa_*`), ou materializa índice `knowledge` enxuto no
alvo; adicionar `knowledge path` por paridade com o AWS.

### P1

**GAP-P1-1 — sem `install manifest`/`install env` e manifests não viajam.**
`forge.json`/`forge.agentic.json`/`manifest.json` ficam fora de wheel e sdist;
nenhum verbo os emite. O sentinel emite `data-sentinel install manifest`
(+`--agentic`) e `install env`. Sem isso, uma instalação PyPI não consegue
publicar sua identidade/capacidades para forge-cli/fleet (item central do
prompt).
Decisão: `install manifest [--agentic]` emitindo a partir de `forge.json` do
pacote (shipá-lo em `_data/` ou `sparkforge_azure/`) com `version` lida do
pacote.

**GAP-P1-2 — `forge.agentic.json` vazio e defasado.**
`version "0.1.0"` (pacote 0.1.6) e `skills:[] agents:[] coordinators:[]`
apesar de 23 skills + 40 agents canônicos + 18 tools MCP existirem. O
manifesto agentico — justamente o documento que anuncia a frota aos hosts —
declara frota zero. Decisão: gerar `forge.agentic.json` a partir de
`agents/CAPABILITY.json` + `mcp catalog` no build (fonte única), travar
`version` ao `__version__`.

**GAP-P1-3 — assimetria de descoberta: marker aponta verbos obsoletos e nada
declara onde knowledge/rules/evals/protocolos resolvem.**
O marker injetado (verificado injetado no alvo) diz `distribution
status|doctor|detach` e `distribution init --with-mirrors`; o lifecycle
canônico é `install *`. E nenhum artefato instalado declara o mapa de
recursos (rules/catalog no pacote, evals no pacote, knowledge via `select`,
políticas nos manifests) — a lista exata de "não descobertos" do §1.
Decisão: atualizar `hostfiles.py` para `install *`; emitir
`forge/ForgeContext/v1` (manifesto de capabilities do Cycle 2) no alvo.

**GAP-P1-4 — sem `MANIFEST.sha256` de assets e locks de superfície não
viajam.**
O sentinel ships `installation/assets/MANIFEST.sha256`. Azure não tem
manifesto de integridade do bundle `_data/`; e `docs/surface.lock.json` +
`docs/claims.lock.json` ficam no checkout → `doctor` em instalação PyPI só
pode reportar `unresolved` (evidência §4.3). Decisão: shippar os locks no
pacote (`_data/` ou `sparkforge_azure/docs/`) e gerar `MANIFEST.sha256` dos
assets no build; `doctor` passa a verificar.

**GAP-P1-5 — `.mcp.json`/`mcp-verify` resolvem por PATH.**
`command: "sparkforge-azure"` depende do PATH do host/shell; pode ligar o
projeto a outra instalação (ex.: bootstrap de `~/.forge` 0.1.0 enquanto o
projeto usa o venv 0.1.6). O AWS grava `sys.executable` absoluto —
determinístico. Decisão: alinhar com o AWS (gravar o executável absoluto +
`-m sparkforge_azure.mcp` / `serve`), mantendo a forma `sparkforge-azure`
como fallback declarado no `forge.json`.

### P2

- **GAP-P2-1**: parser aceita `--host copilot|all` mas `distribution/hosts.py`
  declara só 3 hosts (sem copilot) — csv também rejeitado. Alinhar tabela e
  parser ou documentar a limitação.
- **GAP-P2-2**: `--host` csv/`none` não expostos (mesmo padrão do AWS);
  `--profile` existe mas a granularidade real é por classe (mirrors on/off).
- **GAP-P2-3**: `knowledge` sem `path` — o único jeito de um host localizar o
  conhecimento empacotado é `select`; não há enumeração de arquivos.
- **GAP-P2-4**: `agents list` no wheel mostra `unevaluated` (correto) enquanto
  `CAPABILITY.json` da fonte diz `ready` — a degradação é honesta, mas nenhum
  artefato explica a diferença (evals dependem de `tests/` que não viajam).
- **GAP-P2-5**: `distribution` e `install` são dois ciclos de vida paralelos
  (`inspect/init/detach` vs `apply/doctor/repair`) — fronteira funciona, mas
  a duplicidade confunde (marker aponta o par errado, GAP-P1-3).
- **GAP-P2-6**: `evals/host_proof` só prova 1 runtime (claude_code) e
  `doctor` reporta `host_proven=0` — sem pipeline contínuo de prova por host.
- **GAP-P2-7**: sdist segue o mesmo padrão de inclusão por profundidade do
  AWS — conferir se mirrors gerados (`.agents/`, `.claude/`) e `docs/`/`scripts/`
  vazam; registrar para ajuste do `include`.

---

## 6. Riscos, compatibilidades, decisões, plano de migração

### Compatibilidades confirmadas

- Wheel/sdist locais **bit-idênticos** ao PyPI 0.1.6 — o auditado = o publicado.
- `distribution inspect` declara e cumpre portabilidade: `source: wheel`,
  `asset_count: 256`, `portable_distribution: true`.
- `install apply/uninstall` completos do wheel puro; ledger sha256;
  marker injetado e lido pelo host (evidência real de descoberta).
- `_installkit.py`, `install.sh`, `forge_bootstrap.py` **byte-idênticos** ao
  AWS e ao sentinel — contrato `forge/*` compartilhado real.
- UTF-8 stdio fix presente (ponto que o prompt pede comparar ao sentinel).
- `agents list` e `skills_agents` resolvem `_data/` corretamente — a
  infraestrutura de resolução wheel-safe existe; só o `doctor` a ignora.
- Footprint de install enxuto (177 vs ~1 498 do AWS) — já alinhado ao
  princípio "copiar só o selecionado".

### Riscos

- `doctor` mente `fail` em instalação saudável → perda de confiança no único
  verbo de saúde; falsos negativos escondem falhas reais futuras.
- `.mcp.json` PATH-based pode conectar o projeto a binário de outra versão —
  divergência silenciosa de capacidades.
- Manifesto agentico vazio → fleet invisível para discovery por registry
  (forge-cli lê manifesto, não vasculha `_data/`).
- Recursos "só no pacote" (knowledge/rules/evals) sem verb de localização nem
  declaração no alvo — o host não sabe que existem.

### Decisões propostas (resumo)

1. Corrigir `doctor.agentic_fleet` para `inventory(data_root())` + teste
   e2e de wheel (P0-1).
2. Render de mirrors reescrevendo refs repo-relativas para verb/MCP +
   `knowledge path` (P0-2).
3. `install manifest [--agentic]`/`install env` + ship dos manifests com
   version dinâmica (P1-1/P1-2).
4. Manifesto de capabilities `forge/ForgeContext/v1` + atualização do marker
   para `install *` (P1-3).
5. `MANIFEST.sha256` de `_data/` + ship dos locks de superfície (P1-4).
6. `.mcp.json`/`mcp-verify` com executável absoluto (P1-5); alinhar hosts
   copilot/csv e documentar perfis (P2).

### Plano de migração sugerido

- **Passo 0** (este ciclo): baselines — sem código de produção.
- **Passo 1**: P0-1 (fix de resolução + e2e wheel) e P0-2 (render de refs +
  `knowledge path`).
- **Passo 2**: P1-1/P1-2 — manifests shippados, `install manifest/env`,
  agentic manifest gerado de `CAPABILITY.json`+`mcp catalog`.
- **Passo 3**: P1-3/P1-4 — manifesto de capabilities no alvo, locks + sha256
  de assets verificados pelo `doctor`.
- **Passo 4**: P1-5 + P2 — MCP path determinístico, tabela de hosts,
  granularidade de perfil.
- Gates por passo: `pytest`, `check_surface_lock.py`, `check_claims.py`,
  `check_portability.py` + novo teste e2e que instala do wheel em tmpdir
  (modelo `tests/e2e/test_install_matrix.py` do sentinel).

---

## 7. Apêndice — comandos executados (seleção)

```bash
git rev-parse HEAD                        # d35305c…
python -m build --outdir /tmp/audit_azure/dist .
unzip -l /tmp/audit_azure/dist/sparkforge_azure-0.1.6-py3-none-any.whl
tar -tf  /tmp/audit_azure/dist/sparkforge_azure-0.1.6.tar.gz
python3 -m venv /tmp/audit_azure/venv
venv/bin/pip install /tmp/audit_azure/dist/*.whl
cd /tmp/audit_azure/proj
sparkforge-azure --version                 # 0.1.6
sparkforge-azure doctor                    # fail: agentic_fleet broken×40
sparkforge-azure agents list               # 40 × unevaluated (correto)
sparkforge-azure distribution inspect --root .
sparkforge-azure install apply --root . --profile full --host all --yes  # 177
sparkforge-azure install uninstall --root . --yes                        # 97
python - <<EOF                             # prova da causa-raiz
from sparkforge_azure.agentic.inventory import inventory
from sparkforge_azure.paths import REPO
from sparkforge_azure.distribution.assets import fleet_root
inventory(REPO); inventory(fleet_root())
EOF
pip download sparkforge-azure==0.1.6 --no-deps -d pypi && sha256sum …   # idêntico
sha256sum sparkforge_azure/_installkit.py   # 37250539… (= AWS = sentinel)
sed -n 439,462p sparkforge_azure/doctor.py  # inventory(REPO) na linha 448
```
