# Roadmap faseado

> Fase 0, item 9 (§294). Cada onda = SDD compacto em `docs/sdd/<onda>/` (define/design/plan/ship +
> evidence) e **um commit por onda** (ou mais, nunca menos). Status real: `parity.yaml`.

## v0.1.0 — Azure Data Engineering Foundation (§258)

| Onda | Fases do prompt | Entrega | Prova mínima |
|---|---|---|---|
| W0 | 0, 1, 2 | Discovery: audit AWS, portability matrix, product definition, ADRs, RFC multi-forge, capability map, shared primitives, roadmap | `aws_audit.json` regenerável |
| W1 | 3 | Fundação do repo: `pyproject`, pacote `sparkforge_azure`, ferramentas (ruff/pytest), `scripts/port_from_aws.py`, teste de camadas, SDD machinery | `pytest`, `ruff` verdes |
| W2 | 4 | Core Agentic OS: trust, context, memory, governor, budget, decision, recovery, stop, info gain, checkpoint, model router | testes portados + testes Azure-contexto |
| W3 | 5 | Economy OS: TokenSave (ladder L0–L6), Context Ledger, Token Ledger, Reconciliation, Cache, profiles, AgentOps, OTel | invariantes observed≠estimated, unknown≠0, bytes≠tokens |
| W4 | 6 | Code Intelligence: Python/PySpark/SQL/Terraform/Bicep/YAML/JSON/notebooks Databricks e Fabric/ADF JSON, incremental fingerprinted, change impact | fixtures por formato |
| W5 | 7 | Graphfy: code/data/azure-resource/knowledge/evidence graphs, workspace manifest, live graph, federation, impact, query | composição só por ID explícito |
| W6 | 8 (parte) | Knowledge base + compiler + freshness/drift + impact graph; 21 skills; agents & 20 specialists | metadados obrigatórios validados |
| W7 | 9, 10 | Spark genérico + Azure identity/storage/network/Key Vault (facts, rules, knowledge) | regras com fixtures positivas/negativas |
| W8 | 11, 12 | Azure Databricks + Unity Catalog (primeiro vertical, §255) + governança multicamada | cenário UC external-location ponta a ponta |
| W9 | 13–19 (foundation) | Fabric, Synapse, ADF, Event Hubs/Streaming, Purview, Observability, FinOps | 1+ regra e 1+ fixture por domínio |
| W10 | 8, 18 | Collectors read-only + redaction + `collect workspace-graph` | redaction red-team |
| W11 | 8 | CLI `sparkforge-azure` completa + MCP (risk, compact, pagination, conformance) + Doctor + Offline Bundle | surface lock |
| W12 | 20 | Forge Lab + Digital Twin + 17 cenários | `lab verify` |
| W13 | 21 | Security / red team (11 ameaças §207) | casos declarados passam |
| W14 | 22 | Supply chain: lock com hashes, SBOM CycloneDX, wheel reprodutível, clean install, CI tiers | `verify_wheel` |
| W15 | 23, 24 | Forge Protocol / The Forger discovery + compat API Forge; parity audit; claims lock; docs finais | `claims verify` |

## v0.2.0 (§259) — profundidade

ADF, Synapse, Event Hubs, Streaming, Purview, FinOps em profundidade (collectors live, mais regras,
cenários Lab com transcript gravado — Tier 3).

## v0.3.0 (§260)

Deep Databricks, deep Fabric, governança avançada, migração (Synapse→Fabric; AWS→Azure §219),
live graph contínuo, Lab avançado.

## v1.0 (§261)

Somente com profundidade **comprovada** (claims + evals) em Databricks, Fabric, ADLS, ADF,
Streaming, Governance, Security, Observability, FinOps, Agentic OS, TokenSave, Graphfy, MCP, Lab.

## Estado medido — v0.1.0 foundation (delivery)

Medido em 2026-10-07 sobre `feat/v0.1.0-foundation-delivery`:

- Suite: **2540 testes verdes** (9 skipped), `ruff` limpo, `check_surface_lock`,
  `check_claims`, `check_knowledge`, `check_skills_agents` verdes.
- Skills: **22 catalogadas** — as 21 de domínio do §157 + `analyze-batch-loop`
  (skill de método; ancora a análise de lote no extrator PySpark e cita `SF-PY-004`).
- Regras: catálogo `SF-PY` (12 regras PySpark) + `routing.yaml` com rotas de estado
  e `AGENT-003` (findings_area → coordenador); `rule_areas` declarado nos manifests.
- Contratos fechados nesta entrega: `parity.yaml` + `manifest.json` gerados por
  `scripts/gen_parity.py`; knowledge com `sources.lock.json` e `offline-manifest.json`;
  goldens OTel; harness SDD agentico; matrix MCP com statuses honestos
  (`delegated_to_sdk`, `unresolved`, `not_applicable` onde o Azure não implementa).
- Divergências intencionais do AWS documentadas: extratores `af.*`/`graph.*` e
  derivadores de facts não portados (medido em `test_harness_untrusted`); áreas de
  regra além de `SF-PY` entram com seus catálogos; verbos `analyze`/`judge`/
  `knowledge`/`agentops`/`sdd` são tool_refs planejados da CLI (superfície
  atual: collect/graph/tokensave/governance/doctor/offline-bundle/lab).

## Estado medido — cycle 2 (vertical de acesso UC/ADLS) — **CLOSED**

`CYCLE_2 = CLOSED` em 2026-10-08 — `docs/cycle2/CLOSURE.md` +
`docs/cycle2/OUTCOME_BRIEF.md`. LOCAL_GATES=PASS; REMOTE_CI=NOT_OBSERVED.

Medido sobre `main` @ `3b280dd` + closure branch `chore/cycle2-closure`:

- Vertical de acesso executável: `sparkforge-azure diagnose --bundle|--suite`
  cobre 10 cenários determinísticos (UC→RBAC→ACL→rede→binding→location→
  bypass→runtime→delta→abstain) com `failure_layer`, `evidence_paths`,
  `access_graph`, `context_quality`, `trust` (DATA_ONLY), `knowledge`
  escopado e receipt por caso.
- MCP runtime real: `mcp` SDK Server sobre o registry `sfa_*` (10 tools no
  Cycle 2; 11 no Cycle 3 com `sfa_diagnose_fabric`), risco declarado,
  annotations derivadas, dispatch com spans AgentOps.
- Graphfy: `graph/access.py` monta a cadeia de acesso tipada com
  provenance; `federate()` faz merge static/live por ARM-id com
  `attr_conflicts`; queries de alto valor em `graph/access_queries.py`.
- TokenSave provado no caso real: benchmark `evals/token_efficient/
  access_case` — baseline 10415 B vs economy 1964 B / balanced|deep
  2981 B; tokens `unresolved` sem provider (docs/tokensave/benchmark.md).
- AgentOps: spans por estágio (`diagnose.*`) no ledger, `agentops
  inspect|timeline|critical-path`, waste patterns (duplicate read/
  collector/knowledge, full-read-after-index-hit), memory com env
  fingerprint, recovery com taxonomia + retry só em classes transientes.
- Knowledge: 6 packs do vertical (`knowledge/packs.yaml`) + compilador
  escopado por `failure_layer` com `excluded_domains` provando que
  fabric/synapse/adf não carregam em caso UC.
- Skills: 22 — as 7 do vertical têm evals `positive`/`negative`/`boundary`.
- Doctor: área `live_collectors` (módulo + SDKs por collector, sem
  credenciais).
- Suite: **2541 testes verdes** (9 skipped) — contagem derivada da execução
  final do closure.

`CYCLE_3 = DELIVERED` — `docs/cycle3/OUTCOME_BRIEF.md`. Branch
`feat/cycle3-fabric-deep`, base `068b922`.

- Segundo vertical executável: `sparkforge-azure diagnose fabric
  --bundle|--suite` cobre 16 cenários determinísticos do Microsoft
  Fabric (workspace→item→OneLake→shortcut→source→lakehouse→runtime→
  sjd→capacity→data_factory) com `failure_layer`, `evidence_paths`,
  `fabric_graph`, `knowledge` escopado, `trust`, receipt e fingerprint
  de ambiente por caso.
- Grafo: layer `fabric` no Graphfy (17 kinds SaaS — nunca ARM).
- Regras: `SF-FAB-*` em `rules/catalog/fabric.yaml` + reuso `SF-PY`.
- MCP: `sfa_diagnose_fabric` (read_only) — catálogo 11 tools.
- Collector: `collectors/fabric.py` export+live (fetch injetado, GETs
  read-only, falhas→unresolved), doctor `fabric_vertical`.
- Knowledge: 6 packs Fabric escopados por layer; isolamento entre
  verticais provado por `excluded_domains`.
- SDD: 5 sub-SDDs fechados com build_reports red→green reais
  (worktree base `068b922`); gate 11/11 features ok.
- Suite Fabric: **16 passed / 0 failed**; suíte total **2599 passed / 9 skipped** (venv 3.12, ~215s).

## Estado medido — cycle 4 (vertical Streaming/RTI) — **DELIVERED**

`CYCLE_4 = DELIVERED` — `docs/cycle4/OUTCOME_BRIEF.md`. Branch
`feat/cycle4-streaming`, base `86b1910` (main pós-PR #7).

- Terceiro vertical executável: `sparkforge-azure diagnose stream
  --bundle|--suite` cobre 22 cenários determinísticos (Event Hubs
  auth/network/capacity → partitions → consumer group → progress/lag →
  checkpoint → state store → schema → Spark → sink → Eventstream →
  Eventhouse/KQL → Activator → cross_environment).
- `delivery.classification` unresolved-first: nunca promove evidência
  ausente a exactly-once; loss é candidato/risco, não fato.
- Grafo: layer `stream` no Graphfy (topology + `finding`/`evidenced_by`
  overlay); MCP `sfa_diagnose_stream` (12 tools); packs
  `vertical: stream` (5); corpus TokenSave `stream_case`.
- Regras `SF-STR-*`/`SF-RTI-*`; routing AGENT-006 →
  `streaming-specialist` (`rule_areas` declarado).
- SDD: 6 sub-SDDs com build_reports red→green reais (worktree
  `.tmp-red-c4` @ `86b1910`, exit 2); gate 17/17 features, 0 refused.
- Suite stream: **22 passed / 0 failed**; 79 testes focados; suíte
  total **2682 passed / 9 skipped** (venv 3.12, ~243s).

## Estado medido — cycle 5 (vertical de migração ADF/Synapse → Fabric) — **DELIVERED**

`CYCLE_5 = DELIVERED` — `docs/cycle5/OUTCOME_BRIEF.md`. Branch
`feat/cycle5-migration`, base `61367a5` (main pós-PR #8).

- Quarto vertical executável: `sparkforge-azure migration
  inventory|assess|plan|validate --bundle` cobre 22 cenários
  determinísticos (estate inventory → compatibilidade → pipelines
  ADF/Synapse → Spark refactor → dados/OneLake → waves → validação).
- Readiness unresolved-first: ausência de assessment nunca é READY;
  divergência oficial-vs-Forge → REVIEW + conflito explícito; ciclo de
  dependência → `plan.status=REVIEW` (ordem nunca fabricada).
- Grafo: layer `migration` no Graphfy (asset nodes + dep edges tipados +
  `migrates_to` com status fechado); MCP `sfa_assess_migration`
  (13 tools — projeção compacta: summary/blockers/waves/unresolved);
  packs `vertical: migration` (5); spans `migration.*` no ledger.
- Regras `SF-MIG-*` (6); routing AGENT-007 → `migration-specialist`.
- Skills `azure-data-factory`/`azure-synapse` promovidas ao regime
  vertical (evals positive+negative+boundary).
- SDD: 7 sub-SDDs com build_reports red→green reais (worktree
  `.tmp-mig-red` @ `61367a5`, exit 2).
- Suite migration: **22 passed / 0 failed**; 46 testes focados; suite
  total **2734 passed / 9 skipped** (venv 3.12, ~276s).

## Estado medido — cycle 6 (agentic runtime hardening) — **DELIVERED**

`prompt_evo_agentic_enginner.md` (3555 linhas, tese "NO AGENT WITHOUT
CONTRACT") implementado em 8 waves na branch `feat/cycle6-agentic-runtime`.
Auditoria inicial: substrato forte já existia (manifests v1, routing
determinístico, governor, handoff DATA_ONLY, budgets). O ciclo formalizou
o restante:

- **AGENT_INVENTORY**: `agentic/inventory.py` + `agents list|inspect` +
  doctor `agentic_fleet`; status fechado
  `ready|partial|manifest_only|broken|unevaluated`; resultado honesto
  40/40 `unevaluated` (contrato completo, evals ainda `[]`).
- **AGENT_CONTRACT_V2**: schema v2 nos 40 manifests
  (`family/domain/mission/inputs/outputs/allowed_tools/denied_tools/
  spawn/stop/handoffs/review_policy/evals`); resolve bug latente de
  `CallPolicy.from_manifest` ler campos inexistentes no v1; +`test-engineer`
  +`evaluation-specialist` (taxonomia 38→40).
- **ROLE_PLANS + SPAWN GATE**: `role_plan_for` derivado do manifest (sem
  segunda tabela); `spawn.py` SPAWN/SKIP/DEFER com information-gain por
  trigger; `explain_route` + `agents route` com decisão por candidato.
- **AGENT_TEAMS**: `agent-teams/*.yaml` (4) = elegibilidade apenas, nunca
  spawn list; audit anti-amplificação (team file não declara privilégio).
- **AGENTOPS_AGENT**: `spans.py` — AgentSpan (lane `agent`), contadores de
  saída, tokens `None`+`unresolved` sem fonte; `AgentExecutionReceipt`;
  waste `empty_agent_spawn`/`duplicate_agent_spawn` (observed); value
  vector sem score mágico.
- **AGENT_LABS_SECURITY**: routing lab (canônico→esperado; multi-domínio),
  negative routing, budget lab; security lab (policy deny, confused
  deputy, impersonation, taint poisoned/suspicious, memória envenenada→
  quarantine).
- **CLOSURE**: `fingerprint.py` (sha256 do contrato da frota) +
  `impact.py` (grafo de invalidação, desconhecido→`unresolved`) +
  `agents fingerprint|impact` (surface lock regerado).
- SDD: 7 sub-SDDs sha-encadeados, gate `test_not_written`→verde real.
- Claims novos: `agentic-fleet-40`, `agentic-fingerprint`,
  `sdd-gate-green` (todos com prova executável).
- Suite agentic nova: **~52 testes** (inventory, contract v2, role_plans,
  spawn, test_eval, teams, spans, labs, security, closure); suite total
  **2791 passed / 9 skipped** (venv 3.12, ~298s).

## Estado medido — skills audit + docs hardening — **DELIVERED**

Auditoria minuciosa das 22 skills (contrato v1, triggers, handoffs, evals,
comandos, vazamento AWS, números fabricados) + evolução documental, em duas
entregas (PR #12 + `feat/docs-factory-evolution`).

- `SKILL_HANDOFF_RESOLUTION`: `migration`→`migration-specialist` (2 skills);
  validador resolve alvo de `## Handoff` contra `SKILL_NAMES ∪ ALL_AGENT_IDS`
  (lazy — aresta `skills→agentmanifest` declarada na medição); recusa nomeada.
- `SKILL_EVAL_KIND_COVERAGE`: as 8 skills não-verticais ganharam casos
  `negative` (domínio adjacente real) + `boundary`; teste exige o par nas 22.
- `SKILLS_REFERENCE_DOC`: `docs/reference/skills.md` **gerado** por
  `gen_skills_doc.py` (scope, triggers, handoffs, evals pos/neg/bnd) com
  teste de sync anti-drift; grill gate do Loop Factory documentado em
  `docs/sdd/README.md` mapeado nos campos do SDD; `cli.md` corrigido
  (`sdd check` era implementado, não planejado).
- Suite total **2793 passed / 9 skipped** (venv 3.12).

## Estado medido — cycle 7 (agentic maturity pass) — **DELIVERED**

`prompt_evo_maturity1.md` ≡ `prompt_evo_agentic_enginner.md` (byte-idêntico) —
maturity pass auditou cada bloco § contra artefatos reais
(`docs/agentic/MATURITY_MAP.md`) e fechou as lacunas, em waves commitadas
(`feat/cycle7-maturity`):

- `AGENT_EVAL_SUITE` (W1): `evals/agents/<id>.yaml` ×20 specialists com casos
  `route_positive`/`route_negative` executados contra `explain_route` real
  (negative exige `no_match`, nunca `below_cap`); `_eval_coverage` agora
  resolve cada entrada contra `tests/`/`evals/` (antes bastava lista
  não-vazia — divergência docstring↔código fechada); 40 manifests declaram
  evals reais → frota **40/40 `ready`** (era 40× `unevaluated`; suite 2818/9).
- `AGENT_MIRRORS` (W2): mirrors de hosts para os 40 manifests —
  `.claude/agents/custom/` + `.agents/agents/` file-per-agent, `name`/
  `description` injetados, drift `missing|stale|orphan` + sync, campo
  `agent_mirrors_in_sync` no strict check.
- `BASE_AGENT_PIPELINE` (W3): `agentic/pipeline.py` declara a cadeia §30
  (11 estágios, 7 required + 4 condicionais) e `plan_pipeline` poda por
  contexto — fast path §32 (evidência completa + low risk) vai direto
  `verifier → synthesizer`.
- `MCP_AGENT_ADMIN` (W4): `sfa_agents_list` + `sfa_agents_explain_route`
  read-only (mesma engine do CLI); superficie 13→15 tools, lock regen.
- `AGENT_DOD_GATE` (W5): `test_agent_dod.py` por família + `agents/
  CAPABILITY.json` gerado + gate de novo agent no CONTRIBUTING.

## Estado medido — cycle 8 (autonomy contract + docs) — **DELIVERED**

`feat/cycle8-autonomy-docs`, continuando o maturity pass:

- `AGENT_AUTONOMY_FIELD` (W1): `autonomy` vira **required** no manifest v2 com
  vocab fechado `L0–L5`; frota inteira ≤ L2 (coordinator/referee L2, roles
  determinísticas L0, demais L1) — §153 "default BOUNDED" vira contrato, não
  convenção. `autonomy_for()` resolve manifest→`AutonomyLevel` fail-closed
  (fora da taxonomia → L0); `autonomy` virou dim medida do inventário.
- `AGENTS_REFERENCE_DOC` (W2): `docs/reference/agents.md` **gerado** por
  `gen_agents_doc.py` (kind/domain/autonomy/risk/evals por agent) com sync
  test anti-drift — par do catálogo de skills.

## Estado medido — cycle 9 (agent runtime execution) — **DELIVERED**

`feat/cycle9-agent-runtime`, prompt `prompt_evo_agent_runtime.md` (244
secoes, 6 P0s). Frota congelada — zero agents novos (§1):

- `RUNTIME_EXECUTION_AUDIT` (W0): classificacao honesta — toda camada
  era planning/gating; zero adapters. 6 runtimes `DECLARED_UNPROVEN`.
- `AGENT_RUNTIME_ADAPTERS` (W1): `agentic/runtimes/` — ExecutionMode/
  UsageStatus/RuntimeStatus/FailureKinds fechados; SpawnResultV2;
  registry runtime->adapter->status->proof; host stubs fail-closed
  (binario+opt-in, nunca finge); playbook/inline executam roles L0 de
  verdade (extractor/inventory/judge/verifier/synthesizer).
- `REAL_AGENT_EXECUTION` (W2): schemas por role §96-103,
  `contract_violation` nomeado, freeform -> provisional (§31); `run_case`
  liga gate->adapter->schema->receipt (§24).
- `REAL_HANDOFF_EXECUTION` (W3): handoff emitido entre estagios,
  admit_handoff re-filtra pelo receiver (§41-42); CaseState §45;
  stage_fingerprint §48; resume §47 — fp identico nao re-executa.
- `RUNTIME_DEGRADATION` (W4): cadeia §77 preferred->playbook->inline;
  degraded_reason obrigatorio (§78-79); retry so transiente 1x (§83-84).
- `AGENT_VALUE_EVAL` (W5): `evals/agent_runtime/` (4 cases, expected,
  configs A-D, reports §75); value_vector §57; necessity §59; custo
  `unresolved` sem provider (§55). Resultado honesto: sem host, ganho
  medido = 0 -> necessity UNRESOLVED/NEUTRAL.
- `AGENT_RUNTIME_SURFACE` (W6): spans com campos §122; CLI
  `agents runtimes|runtime-inspect|execute --dry-run|compare`; MCP
  `sfa_agents_runtimes`+`sfa_agents_execution_explain` (17 tools);
  doctor `agent_runtime`.
- `AGENTIC_ARCHITECTURE_FREEZE` (W7): security lab §112-120 verde;
  `freeze.py` mede as 6 condicoes -> **FREEZE_STATUS=candidate**
  (blockers: host_proof_missing, value_eval_unresolved_without_host) —
  freeze so com prova de host (§176).

## Estado medido — cycle 10 (host proof + real eval) — **DELIVERED**

`feat/cycle10-host-proof`. Os binarios de host existem no PATH —
o blocker #1 do freeze era resolvivel de verdade:

- `HOST_PROOF_RECORDED`: `evals/host_proof/<runtime>.json` = transcript
  real (`status=completed` + `trace_ref sha256`); `HostCLIAdapter.status`
  deriva do artefato — prova valida promove a `host_proven`, ausente ou
  corrompida nunca promove. `ClaudeCodeAdapter.postprocess` extrai
  `result` + usage do envelope JSON -> tokens/custo `measured`.
- `claude_code` = **host_proven** (ping minimo $0.66 medido); devin_cli,
  devin_desktop, codex seguem `adapter_implemented` ate prova propria.
- `REAL_HOST_EVAL`: `evaluate_case_host` roda config B real — 1 spawn de
  specialist por vertical via `claude -p`, output DATA_ONLY parseado e
  validado por schema. 4/4 completed, 0 violacoes, necessity USEFUL x4,
  custo total medido **$2.79**. Reports: `reports/<case>.host.json`.
- `evaluate_freeze()`: **FREEZE_STATUS=frozen** — 6/6 condicoes met com
  evidencia nomeada. Regressao de prova volta a `candidate` sozinha.
- Suite total **2907 passed / 9 skipped** (venv 3.12, ~411s).

## Estado medido — cycle 11 (paridade AWS↔Azure) — **DELIVERED**

`feat/cycle11-economy-parity`. `prompt_evo_economy.md` §199-212:

- `W0` baseline + `parity/aws-azure.yaml` (21 capabilities) + gate
  `scripts/check_aws_parity.py` (provas tem que existir).
- `W1` `adapters/upstream.py`: intake `upstream-facts/v1` nos 4 casefiles —
  identidade estrangeira preservada, chaves de instrucao recusadas,
  bounds 256KiB/128.
- `W2` `scripts/check_recall_economy.py`: gold set real derivado (12
  perguntas ancoradas em simbolo .py), nominal 12/12, conceitual 0/12
  reportado, economia `unresolved` nomeada (corpus < envelope 747B/call).
- `W3` `evals/token_benchmark.py` + gabarito `benchmark_cases.yaml`:
  15 casos x 3 profiles = 45/45 celulas; deep escala (debate/reviewer/
  specialist), economy/balanced unresolved; `tokens_unresolved` declarado.
- `W4-W7` medidos: evals/receipt/context/codeintel equivalentes; agentic
  e graphfy **AZURE_AHEAD** (superset estrito + 17 modulos `graph/`).
- `W8` envelope comum §118: intake aceita o rotulo AWS +
  `write_upstream_facts` emissor (round-trip provado).
- `W9` supply chain: verify-lock ok, audit offline 0 findings, SBOM
  CycloneDX, `verify_wheel` reproduzivel (sha256 fd5b3c...).
- `W10` `docs/parity/ECONOMY_PARITY.md`; `W11`
  `AZURE_ARCHITECTURE_FREEZE_READINESS.md` = **ready** (8/8 §133);
  `W12` `AWS_AZURE_PARITY_OUTCOME.md`.
- Correcao real achada pela paridade: `_no_nivel` so media `symbols` —
  `score_breakdown` tambem vive em `entry_points`; `summary` agora reduz
  9.6% medido (13976 vs 15464 bytes).

## Estado medido — pos-freeze (retrieval de identificador composto) — **DELIVERED**

`feat/cycle7-retrieval-docs`. Segunda iteracao medida do gate de economia
na arvore (SDD `TREE_ECONOMY_MEASUREMENT`, AC4):

- Escore `exact_name` por fatia contigua falhava quando **stopword no meio
  do nome** quebrava a fatia: `impact_for` expande para literais `[impact]`
  (`for` e stopword) e `[impact, for]` nao e fatia de `[impact]` — o
  simbolo errado (`impact`) vencia por igualdade com literal solto.
- Fix: `escore(..., identificadores=)` — igualdade do nome normalizado
  contra o identificador composto da pergunta, passado por parametro;
  `_identificadores(tarefa)` ja alimentava a busca de frase FTS em
  `_candidatos()`. Nada e publicado em `expansao.literais` (o invariante
  "pack nao ecoa texto cru da pergunta" segue coberto por teste).
- Recall nominal na arvore: **221/226 -> 224/226** medido. Residuais
  honestos e nomeados no gate: `codeintel/extract.py::No` (stopword
  integra — a expansao filtra a pergunta inteira) e
  `collectors/unity_catalog.py::collect_live` (ambiguo — 4 collectors
  definem o mesmo nome; o pack carrega um dos irmaos).
- `azure/memory.py` permanece declarado `doc-only`: nenhum consumidor
  real existe hoje — o retrieve/record e um adaptador pronto para a
  camada agêntica; ligar `diagnose` (verbo read-only) a escrita de
  `.sparkforge-azure/memory/` seria decisao de produto, nao bug.
- Suite total **2966 passed / 9 skipped** (venv 3.12, ~394s) — inclui
  hardening de skills/agents + distribuição portável W1–W3
  (distribution/workspace/relocatable identity).
