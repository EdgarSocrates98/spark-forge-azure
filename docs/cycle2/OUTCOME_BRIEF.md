# Cycle 2 — outcome brief

```text
STATUS          Cycle 2 acceptance criteria satisfied — CLOSED

BASE_SHA            b1caf70280a95479f4dcd9bb98b119b46ce823e5  (main antes do Cycle 2)
IMPLEMENTATION_SHA  7c09c17  (último commit de código no PR #3; tip do PR: ff28659)
HARDENING_SHA       84a7761  (último commit de código/proof-fix no PR #4)
FINAL_CODE_SHA      84a7761
FINAL_EVIDENCE_SHA  38860e8  (claims stamp; só docs/lock depois do código)
FINAL_MAIN_SHA      3b280dd  (merge do PR #4 em main)

TESTS        2541 passed, 9 skipped — pytest ~3min, Python 3.12.13 (.venv)
LOCAL_GATES  PASS — pytest, ruff, check_surface_lock, check_claims --stamp,
             check_knowledge, check_skills_agents, sdd checks
REMOTE_CI    NOT_OBSERVED — quota GitHub indisponível; nunca declarado green
```

## P0-A — MCP_RUNTIME

Runtime real: SDK `mcp` 2.3.0 `Server` sobre o registry `sfa_*` — stdio
(`python -m sparkforge_azure.mcp`), `tools/list`, `tools/call`, input/output
validation (jsonschema), risk default-deny, trust envelope, spans por call.
10 tools composicionais; inspector-por-API recusado
(`docs/reference/mcp-tools.md`). Matrix `evals/mcp-conformance/matrix.yaml`:
16 covered, 5 delegated_to_sdk, 2 not_applicable, 0 unresolved.

## P0-B — DATABRICKS_UC_ADLS

Vertical deep_local: `diagnose --bundle|--suite` — 10/10 cenários
determinísticos (UC→RBAC→ACL→rede→binding→location→bypass→runtime→delta→
abstain). Facts→Rules→Findings, `failure_layer`, `evidence_paths`
finding→facts→artefato, `unresolved` com `artifact`/`artifact_present`,
receipt por caso. `SF-ACC-001..013` (4 no catálogo + estruturais).

## P0-C — GRAPHFY

`graph/access.py` no hot path: a cadeia de acesso tipada alimenta
`evidence_paths` (derivado do grafo, não bookkeeping paralelo). Federação
static/live por ARM-id com `attr_conflicts`; queries bounded em
`access_queries.py`. Overhead medido: `report.overhead.graph`
(nodes/edges/build_ms/serialized_bytes) + `overhead.stages` por estágio.

## P0-D — TOKENSAVE

Benchmark medido (corpus `evals/token_efficient/access_case`, 11 arquivos):
baseline 9920 B; economy 1964 B; balanced/deep 2981 B — `required_recall`
1.0 nos três, `STOP_SUFFICIENT` em L1, `tokens: unresolved` (sem provider).
Frontier por eixos, sem score agregado. `docs/tokensave/benchmark.md`.

## AGENTOPS

Spans `diagnose.*` (7 estágios/caso) no ledger; CLI
`agentops runs|inspect|timeline|critical-path` lê `state_dir()` (honra
`SPARKFORGE_AZURE_STATE_DIR` — bug de assimetria write/read corrigido no
closure). Critical-path é aproximação temporal — nome mantido honesto.

## CONTEXT_QUALITY

`selected`, `used`, `cited`, `consumed_bytes`, `required`,
`required_present`, `required_recall` — denominador é o required-evidence
set (chain + findings), nunca o selected.

## TRUST

Todo output do vertical = `authority: data_only`; `_trust` envelope em MCP.
Metadados hostis (tag/comment/notebook/tool result) → `suspicious`,
nunca instrução — provado em `tests/test_security_taint.py`.

## SECURITY

Redaction na fronteira de extração (`extract_all` chama
`collectors.redact`): SAS, client secret, storage key, bearer token,
connection string nunca chegam a Fact/Finding/Graph/Report/Memory.
Cross-env (tenant/subscription/workspace/metastore divergente) → finding
`SF-ACC-013` `cross_environment`, nunca merge silencioso.

## MEMORY

`environment_fingerprint` (catálogo/UC + conta ADLS + compute) — memória
de caso só reutilizada quando fingerprint compatível; divergência explícita.

## RECOVERY

Taxonomia `FailureClass` (authn/authz/network/rate_limit/unsupported/
invalid_input/unknown); retry só em classes transientes com fingerprint por
tentativa; fallback `--fallback-export` produz `status=degraded` + receipt
visível; nunca retry oculto.

## KNOWLEDGE

6 packs (`knowledge/packs.yaml`) escopados por `failure_layer` via
`compile_access_knowledge`; `excluded_domains` prova que fabric/synapse/adf
não carregam em caso UC. `check_knowledge` verde.

## SKILLS

22 catalogadas; as 7 do vertical (`azure-adls`, `azure-databricks`,
`azure-entra`, `azure-networking`, `delta-lake`, `spark-performance`,
`unity-catalog`) têm evals `positive`/`negative`/`boundary` validados.
Nenhuma skill criada no closure.

## DOCTOR

17 checks, `network_calls: 0`, `cloud_mutation: none`. `live_collectors`
(módulo + SDKs por collector, `unavailable` offline sem falhar) e
`access_vertical` (catálogo SF-ACC, ids únicos, fixtures, redact boundary).

## CLAIMS

10 claims com prova executável em `docs/claims.lock.json`. `suite-green`
endurecido: padrão ancorado `\n<passed> passed` rejeita prefixos
`N failed,`/`N errors` — regression test em `test_cycle2_evolution.py`.
Proofs rodam com `SPARKFORGE_AZURE_STATE_DIR` apontando tmpdir — worktree
limpo garantido (gaps de residue resolvidos no closure).

## SURFACE

`surface.lock.json` verde; 10 MCP tools + CLI estável. Nenhuma surface
nova criada no closure — drift inexistente por construção.

## SUPPLY_CHAIN

Gates existentes verdes (lock, wheel, clean install, SBOM, dependency
checks na suite). Zero dependências novas no closure.

## DEFERRED / DEFERRED_EXTERNAL / BACKLOG

| Item | Status | Cycle 2 blocker? |
|---|---|---|
| Live Azure collector proof | DEFERRED_EXTERNAL | No — Tier 4 opt-in |
| Provider token observation | DEFERRED_EXTERNAL | No — `tokens=unresolved` é o honesto |
| Persistent live cache | BACKLOG | No — in-memory por decisão |
| Recorded Tier-3 transcripts | BACKLOG | No |
| Fabric deep vertical | NEXT CYCLE | No |
| ADF / Synapse / Event Hubs deep | FUTURE | No |

## CYCLE2_CLOSURE

Cycle 2 closed — todos os critérios de aceite satisfeitos com evidence
executável, sem blocker conhecido (nenhum P0 bug, MCP íntegro, access suite
10/10, Graphfy no hot path, TokenSave honesto, sem secret leakage, claims
sem falso positivo).

## NEXT

Cycle 3 candidate: **Microsoft Fabric deep vertical** — gate de entrada:
outcome/claims/surface/tests/docs sincronizados (este documento).
