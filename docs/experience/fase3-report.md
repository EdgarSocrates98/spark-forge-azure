# FASE 3 — Spark Forge Azure como plataforma agentic de referência

Relatório de fechamento da FASE 3 do `prompt_evo_foco1.md`. Cada item cita
a evidência que o sustenta; nada aqui é promovido por conveniência.

## §3.1 — Padronização (contratos FASE 0)

| Requisito | Estado | Evidência |
|---|---|---|
| Ciclo de vida de install | FEITO | `sparkforge-azure install --yes` rodado em scratch real (`sfa-e2e`): `install status` → `healthy`, `distribution.status: initialized`. Receita documenta `install status`/`doctor`/`repair`/`uninstall`. |
| Recibo honesto | FEITO | Installkit canônico re-vendored (`255b54f`) — `--host codex` em escopo projeto emite `mcp-scope:codex NOT_APPLICABLE`. |
| Superfícies | FEITO | 79 comandos CLI documentados, 18 tools MCP (`sfa_*`); `check_docs_surface` e `check_surface_lock` verdes. |

## §3.2 — Agent-First / host experience

| Item | Estado | Evidência |
|---|---|---|
| `sparkforge-azure ai` | FEITO | Observa devin/claude/codex (binário, versão, auth, integração via `install.service`); `--launch` exige TTY + flag explícita; recusas nomeadas; saída de auth nunca copiada ao recibo. |
| `sfa_ai` (MCP) | FEITO | Read-only, domínio `core`; nunca lança host — launch é fronteira humana CLI+TTY. Handshake real: 18 tools, `sfa_version` invocado. |
| Devin | FEITO | Host-nativo: `devin mcp list` no scratch lista `sparkforge-azure` (cmd `sparkforge-azure mcp serve`); `ai devin` → `READY`, `logged_in: true`, integração `healthy`. |
| Claude | FEITO | `.claude/skills` aterrissou no install; `ai claude` observado. |
| Codex | FEITO | Limitação de MCP projeto-escopo declarada no recibo via installkit canônico. |
| Agents | FEITO | 40 agents na taxonomia; `agents list` → `ready: 40` num projeto instalado; `agents route` selecionou `fabric-specialist`/`adf-specialist`/`streaming-specialist` conforme a query. |
| Execution | FEITO | `agents execute "<tarefa>"` — dry-run honesto com `stage_fingerprints` sha256 reais; nenhum host executado. |
| Skills | FEITO | 22 skills em `.devin/skills/` + mirrors `.claude/`/`.agents/` no install do scratch. |

## §3.3 — Documentação PT-BR

13 receitas em `docs/learn/recipes/` (`instalacao`, `primeiro-uso`,
`analise-azure`, `fabric`, `adf`, `synapse`, `streaming`, `usar-agents`,
`usar-skills`, `verificar-mcp`, `graphfy`, `economia`, `abrir-host`),
indexadas em `docs/learn/README.md` e `docs/README.md`, todas com
comandos executados de verdade e explicação why/when por comando
(commit `6c4f4e9` + correções de sintaxe verificadas no E2E).

## §3.4 — E2E real (projeto scratch)

Sequência executada de verdade num diretório fora do repo:

1. `install --yes` → `healthy`
2. `doctor` → saúde local
3. `analyze pyspark --path . --out facts.json` → `ok`, facts com âncora
4. `judge --facts facts.json` → rules aplicadas, `skipped` honestos
   (`requires_facts` quando o fact não existe)
5. `install mcp-verify` → handshake real PASS, 18 tools
6. `diagnose --suite` — access 10, fabric 16, stream 22, migration 22
   casos verdes
7. `graph` — build 92 nós, 0 unresolved
8. `agents route|execute` — rotas + fingerprints reais
9. `ai` → devin READY; `devin mcp list` nativo lista o server

## Bugs reais encontrados pelo E2E e corrigidos

| Bug | Correção |
|---|---|
| `install mcp-verify` retornava `PASS` maiúsculo → exit 1 num verify bem-sucedido | `main.py` normaliza `status.lower()` |
| `agents *` e `sfa_agents_list` liam `root="."`/`Path.cwd()` → crash `FileNotFoundError` e frota all-broken num projeto instalado | `fleet_root()` em `paths.py` (folha do kernel); call sites em `cmd_agents`, `agent_tools`, `runtimes/generic`; `_has_role_plan` ganhou `root` — regressão `test_agents_verbs_resolve_fleet_outside_repo` |
| Arestas de camada não declaradas (`distribution→install`, `mcp→distribution`, `agentic→paths`) | Declaradas com razão em `EXCECOES_MEDIDAS` |
| Receitas documentavam `analyze pyspark <file>`, `judge` bare, `agents route --prompt` | Corrigidas para `--path`, `--facts`, posicional — verificado no parser real |
| 10 erros ruff pré-existentes (S110/E741/F541/I001/B017) | Gate lint limpo no HEAD |

## Gates finais

| Gate | Resultado |
|---|---|
| `ruff check sparkforge_azure tests scripts` | limpo |
| `pytest -q` | **3025 passed, 9 skipped** (~481s) |
| `check_surface_lock.py` | ok |
| `check_docs_surface.py` | ok (79 cmd, 18 tools, 0 faltantes) |
| `check_docs_index.py` | ok |
| `check_portability.py` | ok |
| `check_claims.py` | 26/28 + `suite-green`/`security-vertical-green` re-provados (--stamp após contagem real) |

## Limitações conhecidas

- `agents list` num wheel instalado sem `tests/`/`evals/` reporta
  `unevaluated` por dimensão — honesto: evals não são empacotados. Em
  checkout fonte (como a venv deste dev), `ready: 40`.
- Copilot segue sem status command documentado (`logged_in: null`).
- Claude MCP de projeto exige aprovação por sessão; Codex MCP só user
  scope — mesma limitação do installkit em todos os forges.
- `test_stale_receipt_lock_is_recovered_only_when_pid_is_absent` falhou
  uma vez sob carga de suíte (lock PID race no Windows); passa isolado e
  a suíte final ficou verde.
