# AWS ↔ Azure Parity Audit — Cycle 11

> PARITY ≠ IDENTICAL CODE. Parity = same engineering guarantee + same evidence
> quality + same maturity level + provider-appropriate implementation.

## Baseline snapshot

| | Spark Forge AWS | Spark Forge Azure |
|---|---|---|
| `MAIN_SHA` | `ab7f02e2423e7c07cc2dbeb982fdc50a2c3f6099` | `b0420b8bbf7161a459e5c2317c312889c35b9a73` |
| version | `0.5.0` | `0.1.0` |
| agentic fingerprint | `89e0ac38af993046` | `84e091bd34e125d7` |
| audit date | cycle 11 | cycle 11 |

Agentic fingerprint = sha256 of the sorted sha256s of every `*.py` under
`sparkforge_*/agentic/` — a change in any file moves the fingerprint.

## Status vocabulary

`ABSENT` / `FOUNDATION` / `PARTIAL` / `MATURE` / `DEEP` / `EVALUATED` /
`PRODUCTION_CANDIDATE` / `DEFERRED`.

Classifications: `AWS_AHEAD` · `AZURE_AHEAD` · `EQUIVALENT` ·
`DIFFERENT_BY_DESIGN` · `DEFERRED`.

Portability: `COPY_SAFE` · `ADAPT` · `REFERENCE_ONLY` · `PROVIDER_SPECIFIC` ·
`DO_NOT_PORT`.

## Method

1. Both repos checked out on `main` at the SHAs above.
2. File-level diff over shared module dirs (`economy/`, `evals/`, `context/`,
   `agentic/`, `scripts/`): shared modules differ almost exclusively by
   namespace (`sparkforge_aws` → `sparkforge_azure`, `~/.sparkforge` →
   `.sparkforge-azure`) — consistent with the `port_manifest.yaml` pipeline.
3. Named AWS gaps were read in full (`adapters/upstream.py`,
   `scripts/check_recall_economy.py`, `evals/token_benchmark.py`,
   `scripts/gen_sbom.py`, `scripts/gen_lock.py`) and mapped to the Azure seam
   they would land on.
4. Every row cites evidence paths on both sides; `unresolved` is recorded
   instead of guessing.

## P0-1 — Economy OS

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| economy profiles (economy/balanced/deep) | MATURE | MATURE | EQUIVALENT | — | `economy/router.py`, `context/gateway_profiles.yaml` both sides |
| agent/case/debate/token/tool/time budgets | MATURE | MATURE | EQUIVALENT | — | `agentic/budget.py`, `agents/budget.py`, `economy/decision_*` both sides |
| retry/replan budgets | MATURE | MATURE | EQUIVALENT | — | `agentic/recovery.py` (retry once, transient-only) both sides |
| context cache / decision cache / eval cache | MATURE | MATURE | EQUIVALENT | — | `economy/cache.py`, `economy/ledger.py` both sides |
| model router | MATURE (SHADOW) | MATURE (SHADOW) | EQUIVALENT | — | `economy/model_router.py` both sides; neither activates by default — correct |
| waste detection | MATURE | MATURE | EQUIVALENT | — | `economy/waste_detector.py` both sides |
| loop fingerprints / repeated-cycle prevention | MATURE | MATURE | EQUIVALENT | — | `agentic/fingerprint.py` (Azure), `decision/fingerprint.py` (both) |
| recall/economy CI gate | MATURE | **ABSENT** | **AWS_AHEAD** | ADAPT | `scripts/check_recall_economy.py` (AWS only) — W2 |

## P0-2 — Recall / retrieval quality

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| recall module | MATURE | MATURE | EQUIVALENT | — | `economy/recall.py` identical modulo namespace |
| gold set derived from rules | MATURE | **PARTIAL** | **AWS_AHEAD** | ADAPT | `economy/goldset.py` exists both sides, but `derivar_goldset()` returns **0 questions** on Azure: fixture findings anchor stage/file facts, not `.py` symbols — W2 names the unblock |
| required-evidence denominator | MATURE | MATURE | EQUIVALENT | — | `economy/recall.py` computes over required evidence, not selected context |

## P0-3 — Evaluation / replay

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| eval runner / suite / grade / compare | MATURE | MATURE | EQUIVALENT | — | `evals/runner.py|suite.py|grade.py|compare.py` both sides |
| decision replay | MATURE | MATURE | EQUIVALENT | — | `evals/decision_replay.py` both sides |
| evidence bundles + resolver + lifecycle | MATURE | MATURE | EQUIVALENT | — | `evals/evidence*.py`, `evals/lifecycle.py` both sides |
| candidate policy / promotion / rollback | MATURE | MATURE | EQUIVALENT | — | `evals/policy.py`, `evals/evolution.py`, `decision/authority.py` both sides |
| token benchmark (Gateway profiles) | MATURE | **MATURE** | EQUIVALENT | ADAPT | `evals/token_benchmark.py` ported this cycle; Azure `benchmark_cases.yaml` gabarito (15 cases × 3 profiles, 45/45 cells pass); `scripts/check_token_efficient_bench.py` gate |
| agent runtime eval (A/B value vector) | ABSENT | **EVALUATED** | **AZURE_AHEAD** | — | `evals/agent_runtime/` + `agentic/agent_eval.py`; 4 real host runs, `$2.79` measured (cycle 10) |
| host replay | MATURE | MATURE | EQUIVALENT | — | `evals/token_efficient/fixtures/host_replay.yaml` both sides |

## P0-4 — Agentic runtime

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| runtime adapter registry + closed vocabularies | ABSENT | **PRODUCTION_CANDIDATE** | **AZURE_AHEAD** | — | `agentic/runtimes/` (Azure only) |
| real host execution + transcript proof | ABSENT | **EVALUATED** | **AZURE_AHEAD** | — | `evals/host_proof/claude_code.json`, `agentic/execution.py` |
| spawn gate / role context plans | MATURE | MATURE | EQUIVALENT | — | `agentic/spawn.py`, `agentic/role_plans.py` both sides |
| handoff admission (DATA_ONLY, receiver revalidation) | MATURE | MATURE | EQUIVALENT | — | `agentic/handoff.py` both sides; Azure additionally wires it into `execution.py` |
| debate / referee / arbitration | MATURE | MATURE | EQUIVALENT | — | `agentic/debate.py|referee.py|arbitration.py` both sides |
| governor / control / stop | MATURE | MATURE | EQUIVALENT | — | `agentic/governor.py|control.py|stop.py` both sides |
| freeze gate (evidence-derived) | ABSENT | **MATURE** | **AZURE_AHEAD** | — | `agentic/freeze.py` — `FREEZE_STATUS=frozen`, 6/6 conditions (cycle 10) |
| degradation chain (preferred→playbook→inline) | FOUNDATION | MATURE | **AZURE_AHEAD** | — | `agentic/runtimes/host.py` + `execution.py` (Azure) |
| security lab (confused deputy, injection) | PARTIAL | MATURE | **AZURE_AHEAD** | — | `tests/test_agentic_security.py` + `agentic/security.py` (Azure) |

## P0-5 — Context / trust / memory

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| context gateway + budgets + profiles | MATURE | MATURE | EQUIVALENT | — | `context/gateway*.py`, `gateway_profiles.yaml` identical modulo namespace |
| trust labels / taint / UNKNOWN floor | MATURE | MATURE | EQUIVALENT | — | `agentic/trust.py`, `context/gateway.py:_item_trust` (UNKNOWN on absent/invalid) both sides |
| memory (applicability, conflicts) | MATURE | MATURE | EQUIVALENT | — | `agentic/memory.py` both sides |
| environment fingerprint scoping | MATURE | MATURE | DIFFERENT_BY_DESIGN | — | boundaries differ by provider (tenant/subscription/workspace/catalog vs account/region/catalog); mechanism equivalent |
| context quality measurement | MATURE | MATURE | EQUIVALENT | — | `context/quality.py` both sides |
| host usage accounting | MATURE | MATURE | EQUIVALENT | — | `context/host_usage.py` both sides; Azure additionally parses real `claude` envelopes |

## P0-6 — Graphfy / code intelligence

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| code graph / resource graph | MATURE | MATURE | DIFFERENT_BY_DESIGN | — | `graph/` both sides; Azure identities are ARM/Fabric IDs, AWS are ARNs |
| codeintel (lineage, impact) | MATURE | MATURE | EQUIVALENT | — | `codeintel/` both sides |
| evidence graph / impact graph | MATURE | MATURE | EQUIVALENT | — | `agentic/graph.py`, `agentic/impact.py` (Azure adds agent impact) |
| federated merge (explicit identity only) | MATURE | MATURE | EQUIVALENT | — | `evals/token_efficient/fixtures/federated_graph_cases.yaml` exercised both sides |
| graph recall measurement | PARTIAL | PARTIAL | EQUIVALENT | — | measured inside token-efficient suite on both; no dedicated gate either side |

## P0-7 — Evidence / claims / receipts

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| content-addressed receipts | MATURE | MATURE | EQUIVALENT | — | `azure/receipt.py` ↔ AWS receipt module |
| claims lock with executable proof | MATURE | MATURE | EQUIVALENT | — | `docs/claims.lock.json` + `scripts/check_claims.py` (Azure), `check_vnext_claims.py` (AWS) — different surfaces, same guarantee |
| tamper checks on eval artifacts | MATURE | MATURE | EQUIVALENT | — | `evals/evidence.py` bundle hashing both sides |
| upstream foreign-facts intake | MATURE | **ABSENT** | **AWS_AHEAD** | ADAPT | `adapters/upstream.py` (AWS only) — **W1 of this cycle** |

## P0-8 — MCP / interoperability

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| tool schema rigor + input/output validation | MATURE | MATURE | DIFFERENT_BY_DESIGN | — | `mcp/tools.py` dispatch + per-tool schemas both sides; tool *sets* differ by product shape (`sfa_*` vs `sparkforge_aws_*`) |
| risk model (read_only/cloud_read/local_write/cloud_write) | MATURE | MATURE | EQUIVALENT | — | `mcp/` risk annotations + default-deny both sides |
| pagination / bounded output | MATURE | MATURE | EQUIVALENT | — | `paginate_items`, `limit`/`cursor` both sides |
| A2A | EXPERIMENTAL | EXPERIMENTAL | EQUIVALENT | — | no interoperable proof either side — stays EXPERIMENTAL |
| The Forge handoff (upstream facts) | MATURE | ABSENT→**W1** | AWS_AHEAD | ADAPT | this cycle delivers the Azure intake |

## P0-9 — Supply chain / release

| capability | AWS | Azure | class | portability | evidence |
|---|---|---|---|---|---|
| hashed dependency lock | MATURE | MATURE | EQUIVALENT | — | `gen_lock.py` (AWS) ↔ `scripts/supply_chain.py lock/verify-lock` (Azure) |
| SBOM (CycloneDX) | MATURE | MATURE | EQUIVALENT | — | `gen_sbom.py` (AWS) ↔ `supply_chain.py sbom` (Azure) |
| offline advisory audit | MATURE | MATURE | EQUIVALENT | — | `verify_offline_bundle.py` (AWS) ↔ `supply_chain.py audit` (Azure) |
| reproducible wheel + installed tests | MATURE | MATURE | EQUIVALENT | — | `verify_wheel.py` both sides |
| surface lock | MATURE | MATURE | EQUIVALENT | — | `check_surface_lock.py` both sides |
| docs index / docs surface gate | PARTIAL | MATURE | **AZURE_AHEAD** | — | `check_docs_index.py`, `check_docs_surface.py` (Azure only) |

## P0-10 — Architecture freeze readiness

| capability | AWS | Azure | class | evidence |
|---|---|---|---|---|
| runtime freeze (agentic) | ABSENT | **frozen** (6/6 conditions, cycle 10) | AZURE_AHEAD | `agentic/freeze.py`, `docs/agentic/AGENTIC_ARCHITECTURE_FREEZE.md` |
| economy freeze readiness | not assessed | **assessed this cycle** | — | `docs/parity/AZURE_ARCHITECTURE_FREEZE_READINESS.md` |

## Gap list (ordered by value)

| # | gap | side | wave | status |
|---|---|---|---|---|
| 1 | foreign-facts intake (`upstream-facts/v1`) | Azure | W1 | **done this cycle** |
| 2 | recall/economy gate (`check_recall_economy.py`) | Azure | W2 | **done this cycle** (gold set unresolved — named, not faked) |
| 3 | token benchmark module (`evals/token_benchmark.py`) | Azure | W3 | **done this cycle** |
| 4 | handoff → host replay parity doc | both | W4 | documented |
| 5 | gold set derivation needs symbol-anchored fixtures | Azure | — | **unresolved** — fixtures anchor stage/file facts; unblock recorded in the gate output |

## Deferred (learned from AWS deferrals)

- **Model router activation** — stays `SHADOW` on both; no real consumer justifies activation. Parity = same deferred state, not forced activation.
- **A2A beyond EXPERIMENTAL** — no interoperable proof exists on either side.
- **Raw cloud-latency comparison** — forbidden by the parity contract; only Forge overhead is compared.

## Wave verification log (cycle 11)

Measured by normalizing `sparkforge_aws` → `sparkforge_azure` and diffing
file contents; "identical" = byte-equal after namespace normalization.

### W4 — evaluation / replay / receipts (§44–58)

| package | shared files | identical after ns | differing |
|---|---|---|---|
| `evals/` | 18 | 14 | `cli.py`, `evidence_adapters.py`, `evolution.py`, `token_benchmark.py` (new this cycle) |
| `receipt/` | 4 | 2 | `build.py`, `verify.py` (Azure-side evolutions) |

All four diffs are Azure-side deltas, not gaps — no AWS eval capability is
missing. Control-plane fixture carries 50 labeled tasks (§45 floor met).
P0-C: **EQUIVALENT**, no code gap.

### W5 — agentic runtime (§61–73)

`sparkforge_aws/agentic/` is a strict subset: zero AWS-only files.
Azure adds the runtime layer AWS never shipped — `runtimes/` adapters,
`execution.py`, `schemas.py`, `freeze.py`, `agent_eval.py`, `spans.py`,
`teams.py`, `inventory.py`, `impact.py`, `pipeline.py`, `fingerprint.py`.
Empirical proof exists only on this side: `evals/host_proof/claude_code.json`
transcript + 4 real host evals ($2.79 measured) + `FREEZE_STATUS=frozen`.
P0-D: **AZURE_AHEAD** — parity does not mean backporting Azure-only value.

### W6 — context / trust / memory (§74–81)

`context/` is 13/13 identical after namespace; `agentic/` shared files
(memory, trust, handoff, role_plans, runtime, stop) identical. Trust floor
(UNKNOWN) and memory conflict preservation hold on both. P0-E:
**EQUIVALENT** — no measured gap to close.

### W7 — graphfy / codeintel (§82–91)

`codeintel/` 18 shared files (11 identical; 7 Azure evolutions). `graph/`
exists only on Azure (17 modules: federation, arm, fabric, workspace,
impact, semantic, store) — the AWS side has no equivalent package.
Canonical identities stay provider-specific (ARM/Fabric IDs vs ARNs) per
§84–85; federation contract (explicit-identity merge, provenance and
conflict preservation) is in `graph/federation.py`. CodeIntel recall is
covered by the W2 gold set (symbol-anchored `.py` findings). P0-F:
**AZURE_AHEAD** on graphfy, EQUIVALENT on codeintel.
