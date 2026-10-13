# Runbook de operação — gates, locks e manutenção

O que rodar, quando regenerar, e o que cada guarda mede. Ordem canônica da
verificação pré-entrega (`AGENTS.md`).

## Gates de verificação

> **Interpretador**: rode os gates com o venv do projeto
> (`.venv/Scripts/python` no Windows). `python` no PATH pode ser outro
> interpretador sem os extras opcionais — `check_claims` roda as provas
> com `sys.executable`, então um stamp feito fora do venv falha com
> erros de coleta que não são do código.

```bash
.venv/Scripts/python -m ruff check sparkforge_azure tests scripts   # lint
.venv/Scripts/python -m pytest -q                                  # suite
.venv/Scripts/python scripts/check_knowledge.py                    # corpus knowledge
.venv/Scripts/python scripts/check_skills_agents.py                # skills/agents/mirrors
.venv/Scripts/python scripts/check_surface_lock.py                 # superfície travada
.venv/Scripts/python scripts/check_docs_surface.py                 # docs cobrem toda a superfície travada
.venv/Scripts/python scripts/check_docs_index.py                   # toda doc indexada no README
.venv/Scripts/python scripts/check_portability.py                  # gate §188: assets, schema, docs, mirrors, paths
.venv/Scripts/python evals/portability/runner.py                   # matriz de portabilidade (10 casos)
.venv/Scripts/python scripts/check_claims.py                       # claims com prova
```

| Guarda | O que mede | Falha típica |
|---|---|---|
| `check_knowledge.py` | IDs, metadata, freshness, manifest offline, paths contidos | entrada sem fonte/`verified_at`; path fora de `knowledge/` |
| `check_skills_agents.py` | contrato v1 de SKILL.md, manifests, mirrors em sync | `knowledge_refs` p/ dir inexistente (use `--allow-pending-knowledge` p/ diagnosticar) |
| `check_surface_lock.py` | CLI commands, MCP tools, compact set, capabilities, counts de skills/knowledge | drift de superfície → `--update` + explicar no commit |
| `check_claims.py` | cada claim em `docs/claims.lock.json`: texto verbatim no doc + prova executada + sha ancestral | doc driftou do lock; sha não-ancestral; prova falha |
| `check_docs_surface.py` | todo comando CLI e tool MCP do surface.lock tem seção nos docs de referência | verbo/tool novo sem doc → documentar em `docs/reference/cli.md`/`mcp-tools.md` |
| `check_docs_index.py` | toda doc authored (`docs/**` fora de `sdd/`/`superpowers/`) é alcançável via `docs/README.md` | doc novo sem entrada no README → indexar na seção certa |
| `check_otel_collector.py` | igualdade semântica traces/metrics vs goldens | decoração de pipeline não conta; atributos semânticos sim |
| `check_skills_agents.py --root X` | valida árvore arbitrária | — |
| `sparkforge-azure doctor` | áreas: `mcp`, `azure_extras`, `live_collectors` (módulo + SDKs por collector), `knowledge_freshness`, `tokensave`, `graphfy`, `access_vertical`, `fabric_vertical`, `streaming_vertical`, `migration_vertical` | `live: unavailable` = extra SDK ausente (modo export offline segue válido); nunca lê credencial |
| `diagnose --suite tests/fixtures/access` | 10 cenários UC/ADLS contra o oráculo `expect:` | failure_layer divergente = regressão de diagnóstico |
| `diagnose fabric --suite tests/fixtures/fabric` | 16 cenários Fabric contra o oráculo `expect:` | idem; `unresolved` nunca é `denied`/`allowed` inventado |
| `diagnose stream --suite tests/fixtures/stream` | 22 cenários Streaming/RTI contra o oráculo `expect:` | `unresolved` nunca é entitlement inventado; delivery semantics não promove sem evidência |
| `migration assess --suite tests/fixtures/migration` | 22 cenários ADF/Synapse→Fabric contra o oráculo `expect:` | readiness ausente ≠ READY; ciclo → REVIEW; conflito oficial → REVIEW |
| `check_portability.py` | gate estático §188: inventário de assets, schema de manifests, docs de portabilidade presentes, mirrors em sync, nenhum path de checkout em config gerada, acesso a HOME só em módulos autorizados, traversal/symlink recusados | vazamento de path de checkout em `.mcp.json`; `Path.home()` em módulo não autorizado; doc de portabilidade ausente |
| `check_portability.py --wheel` | T3: builda a wheel, instala num venv temporário fora do checkout e corre `inspect→init→status→detach→init` do binário instalado | command `sparkforge-azure` ausente; manifesto/assets faltando na wheel |
| `evals/portability/runner.py` | matriz §96–§101 — 10 cenários (single/monorepo/multi-repo/relocate/copy/scopes/detach/mcp-only/host-unavailable) em temp dirs com HOME/XDG falsos; grava `reports/portability-matrix.json` | caso `ok`→falha é regressão do lifecycle; `refused` esperado = recusa nomeada, nunca exceção |

## Regeneração de locks (nunca editar à mão)

| Lock | Comando | Quando |
|---|---|---|
| `docs/surface.lock.json` | `python scripts/check_surface_lock.py --update` | mudou CLI/MCP/skills/knowledge counts |
| `docs/claims.lock.json` | `python scripts/check_claims.py --stamp` | claim novo/doc mudou; prova roda e carimba sha=HEAD |
| `parity.yaml` + `manifest.json` | `python scripts/gen_parity.py` | `port_manifest.yaml`/`aws_audit.json` mudou ou pacote cresceu |
| `knowledge/INDEX.md` + `sources.lock.json` + `offline-manifest.json` | `python scripts/refresh_knowledge.py --report` / regen INDEX | fonte knowledge adicionada/atualizada |
| mirrors `.agents/`+`.claude/skills/` | `python scripts/sync_skill_mirrors.py` | skill criada/editada (`--check` só reporta drift) |
| goldens OTel | `scripts/check_otel_collector.py --goldens fixtures/otel/<case>` | comportamento de export mudou (regen consciente) |

## Manutenção recorrente

| Tarefa | Comando |
|---|---|
| Freshness de fontes knowledge | `python scripts/refresh_knowledge.py --report` (só GET http(s), sha256 da página) |
| Auditoria de port AWS↔Azure | `python scripts/aws_portability_audit.py` |
| Portar arquivo do AWS | só via `python scripts/port_from_aws.py` + `scripts/port_manifest.yaml` |
| Verificar wheel | `python scripts/verify_wheel.py` |
| Rodar eval agentico SDD | `python scripts/run_agentic_eval.py` (baseline em `evals/agentic/sdd/`) |

## Recusas comuns e o que significam

- `knowledge dir '...' does not exist` — `knowledge_refs` em skill/agente aponta
  para diretório ausente; criar o dir ou declarar `--allow-pending-knowledge`.
- `surface drift` — superfície pública mudou sem regen; rode `--update` e
  explique no commit (mudança de superfície é decisão, não detalhe).
- `sha <x> is not an ancestor of HEAD` — claim carimbado em commit que não
  antecede o HEAD atual; re-stampe com `--stamp`.
- `risco desconhecido → DENY` — tool MCP sem `risk` ou com dimensão fora da
  lista; declarar `ToolRisk` correto em vez de relaxar o gate.

## Estado local (fora do git)

`.sparkforge-azure/` — journal append-only (`journal.jsonl`), cases, grafos,
índices. `.pytest-tmp/` — basetemp do pytest (ignorado por `iter_source_files`).
`.claude/agents/` — estado local vestigial (não commitado).
