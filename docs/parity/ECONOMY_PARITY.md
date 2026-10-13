# Economy Parity — AWS ↔ Azure (cycle 11)

Deep dive §135–136 of `prompt_evo_economy.md`: mechanism-by-mechanism
comparison. "Equivalent" means the mechanism exists with the same honesty
contract — measured-or-unresolved, never invented — not the same numbers.
Cloud latency and provider pricing are out of scope by contract; only Forge
overhead and artifact sizes are compared.

| area | AWS mechanism | Azure mechanism | equivalent? | proof | remaining gap |
|---|---|---|---|---|---|
| TokenSave context | `tokensave` MCP + CLI wrapper | `sparkforge-azure tokensave context` + tokensave MCP | yes | `cli/` tokensave verbs; MCP `sfa_*` tools | none |
| recall/economy gate | `scripts/check_recall_economy.py`, floor 27 | `scripts/check_recall_economy.py`, floor 12 | yes (different floor) | gate output: nominal 12/12, conceptual 0/12, economy unresolved | corpus too small for economy ratio — unlock named in gate output |
| budgets | `economy/` contract + ledger | `economy/` — 15/20 files identical after namespace | yes | `decision_models.BudgetSnapshot`, `ledger.TokenLedger` | none |
| gateway profiles | economy/balanced/deep envelopes | same three profiles, Azure byte envelope measured (747 B/call) | yes | `context/gateway_profiles.yaml`, W2 gate output | none |
| cache | `decision/cache.py` artifact/decision/fact namespaces | same file ported | yes | `decision/cache.py`, `gateway_refs.ContextRefStore` | none |
| graphfy | no `graph/` package | `graph/` — 17 modules (federation, arm, fabric, impact…) | **Azure ahead** | `sparkforge_azure/graph/` | none on Azure |
| codeintel | `codeintel/` 18 files | 18 files, 11 byte-identical after ns | yes | module diff (cycle 11 audit) | none |
| agents (economy) | no runtime layer | runtimes + host evals, cost measured $2.79/4 runs | **Azure ahead** | `agentic/agent_eval.py`, `evals/agent_runtime/` | none on Azure |
| replay | `evals/decision_replay.py` | same file, identical after ns | yes | cycle-11 diff | none |
| token benchmark | `evals/token_benchmark.py` | ported this cycle — 45/45 cells | yes | `sparkforge_azure/evals/token_benchmark.py`, `evals/parity/token_benchmark_baseline.json` | provider tokens unresolved (no host transcript in bench) |
| provider tokens | measured only via host transcript | same rule — `provider_tokens=None`, `tokens_unresolved=True` | yes | benchmark matrix (45/45 cells, all unresolved) | real provider usage needs a host run per case |
| cost | price profiles only when declared | `ProviderPriceProfile` + measured host cost | yes | `economy/ledger.py`, cycle-10 host evals | none |
| latency | Forge-side only (contract) | same | yes | — | none |

## Measured numbers this cycle

```text
benchmark matrix      15 cases x 3 profiles = 45 cells, all gabarito-pass
payload_bytes         median_low ~2.7 KB / max ~3.6 KB per answer (all profiles)
plan differentiation  deep: debate×2, reviewer×3, specialist×3, unresolved×4,
                      deterministic×1; economy/balanced: unresolved×12 + 1 det
recall (W2)           nominal 12/12, conceptual 0/12 (reported, no floor)
economy ratio         UNRESOLVED — corpus 1433 B < envelope 8964 B for 12 calls
                      (fixed envelope 747 B/call); unlock: corpus > envelope
tokens                unresolved in all cells — no provider basis
```

## Honest asymmetries kept

- Recall floor is **12** on Azure vs **27** on AWS — floors are corpus-derived,
  not copied (§: "nao se copia threshold sem corpus proprio").
- Economy ratio stays `unresolved` on the current fixture corpus; publishing a
  ratio there would violate small-corpus honesty (§39).
- `provider` tokens are `None`/`unresolved` everywhere the bench runs without
  a host transcript — unknown is not zero (AGENTS.md invariant 4).
