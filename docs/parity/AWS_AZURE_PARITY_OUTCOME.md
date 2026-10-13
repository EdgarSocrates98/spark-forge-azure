# AWS ↔ Azure Parity Outcome (cycle 11)

Machine-readable summary per `prompt_evo_economy.md` §213–214.

```text
AWS_MAIN_SHA       ab7f02e2423e7c07cc2dbeb982fdc50a2c3f6099
AZURE_BASE_SHA     b0420b8bbf7161a459e5c2317c312889c35b9a73
AZURE_FINAL_SHA    9442254616dff1912c3d9b2578ab2b9dddfa2649

CAPABILITIES_AUDITED 21

EQUIVALENT_COUNT         13
AWS_AHEAD_COUNT           0
AZURE_AHEAD_COUNT         4
DIFFERENT_BY_DESIGN_COUNT 2
DEFERRED_COUNT            2

ECONOMY       EQUIVALENT — economy/ 20 modules; profiles parity; bench matrix 45/45
RECALL        EQUIVALENT — gate green: nominal 12/12, conceptual 0/12 reported,
              economy unresolved on small corpus (named unlock)
EVALUATION    EQUIVALENT — evals/ 18 shared files; token_benchmark ported;
              compare refuses mismatches
AGENTIC       AZURE_AHEAD — runtimes + host proof + value eval; freeze frozen 6/6
CONTEXT       EQUIVALENT — context/ 13/13 identical after namespace
TRUST         EQUIVALENT — UNKNOWN floor identical
MEMORY        EQUIVALENT — conflict preservation identical
GRAPHFY       AZURE_AHEAD — graph/ 17 modules; AWS has none
CODEINTEL     EQUIVALENT — codeintel/ 18 shared (11 identical, 7 Azure evolutions)
MCP           EQUIVALENT — same governance/schema/pagination/risk discipline;
              compact mode; A2A EXPERIMENTAL both sides
INTEROP       EQUIVALENT — upstream-facts intake + common envelope + emitter
              (W8); The Forge can route Azure→AWS with no translator
EVIDENCE      EQUIVALENT — receipt/ build+verify; content-addressed bundles
CLAIMS        EQUIVALENT — check_claims gate; measured-or-unresolved rule held
SUPPLY_CHAIN  EQUIVALENT — supply_chain.py (lock/verify/sbom/audit) green;
              verify_wheel reproducible sha256 fd5b3c…, clean-venv install

BENCHMARKS    evals/parity/token_benchmark_baseline.json — 15 cases x 3
              profiles = 45 cells, all gabarito-pass; payload median_low
              ~2.7 KB; deep escalates (debate/reviewer/specialist) where
              economy/balanced stay unresolved; tokens_unresolved=45
              (no provider transcript — declared, not zero)

ARCHITECTURE_FREEZE_STATUS  ready — 8/8 §133 conditions met with named proof
                            (docs/parity/AZURE_ARCHITECTURE_FREEZE_READINESS.md)
```

## What this cycle changed

| wave | deliverable | commit subject |
|---|---|---|
| W0 | baseline snapshot + `parity/aws-azure.yaml` + `check_aws_parity.py` gate | `parity: baseline snapshot + capability audit…` |
| W1 | upstream-facts intake (`adapters/upstream.py`) wired into 4 casefiles/pipelines | `upstream: …(W1)` |
| W2 | real gold set (12 symbol-anchored questions) + recall/economy gate | `recall: gold set real derivado…(W2)` |
| W3 | `evals/token_benchmark.py` ported; `benchmark_cases.yaml` gabarito; bench gate + baseline | `benchmark: token-efficient matrix…(W3)` |
| W4 | eval/replay convergence measured — no code gap | `audit(W4)` |
| W5 | agentic measured strict-superset — AZURE_AHEAD | `audit(W5)` |
| W6 | context/trust/memory identical — no gap | `audit(W6)` |
| W7 | graphfy Azure-ahead; codeintel equivalent | `audit(W7)` |
| W8 | common handoff envelope + `write_upstream_facts` emitter | `interop: envelope de handoff comum…(W8)` |
| W9/W10 | supply chain gates green + SBOM + `ECONOMY_PARITY.md` | `release(W9)` |
| W11 | `AZURE_ARCHITECTURE_FREEZE_READINESS.md` — 8/8 met | `freeze(W11)` |
| W12 | this outcome + final gates + PR | — |

## Deferred, deliberately

- **Model router activation** — `SHADOW` both sides; no consumer justifies it.
- **A2A beyond EXPERIMENTAL** — no interoperable proof exists on either side.
- **Raw cloud-latency comparison** — forbidden by contract; Forge overhead only.
- **Economy ratio on the fixture corpus** — `unresolved` until corpus > envelope;
  the gate refuses to fabricate it.
