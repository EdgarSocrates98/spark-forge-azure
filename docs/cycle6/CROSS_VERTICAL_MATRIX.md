# Cycle 6 — Cross-Vertical Matrix

`prompt_evo_cycle6.md` §9. Medido sobre `feat/cycle6-convergence`.
Legenda de uso real: **H** = hot path do `run_case`; **S** = superficie
(MCP/CLI/evals); **-** = ausente.

| Capability | Databricks | Fabric | Streaming | Migration | Shared contract | Shared impl | Provider specialization | Known divergence | Action |
|---|---|---|---|---|---|---|---|---|---|
| Facts/Rules/Findings | H | H | H | H | `Fact`/`Finding` em `facts/`+`findings/` | mesmos loaders e judge | regras por vertical | nenhuma | — |
| Receipt | H | H | H | H | `receipt`+`evidence_paths`+`overhead` | `receipt/`+`decision/` | nome do graph key muda | fechada W1: migration emite `evidence_paths` | — |
| Graphfy | H | H | H | H | nodes/edges tipados + proveniencia | `graph/` | `access/fabric/stream/migration_graph` | ids por dominio (§14) | — |
| Knowledge | H | H | H | H | `knowledge` no resultado | `knowledgebase/` | packs por vertical | nenhuma | — |
| Trust DATA_ONLY | H | H | H | H | `taint`/`trust` no resultado | `agentic/trust.py` | — | nenhuma | — |
| AgentOps | H | H | H | H | `stages`/`overhead` + spans | `observability/` | stage names por vertical | nenhuma | — |
| Upstream facts | H | H | H | H | `upstream-facts/v1` | `adapters/upstream.py` | — | nenhuma | — |
| Context Gateway | S | S | S | S | ContextPack/profiles | `context/` | — | pipelines nao montam pack (design §10) | documentar |
| TokenSave | S | S | S | S | progressive retrieval | `context/progressive.py` | — | idem | documentar |
| Code Intelligence | S | S | S | S | indice+pack | `codeintel/` | — | idem | documentar |
| Memory | - | S | - | - | env-scoped records | `azure/memory.py` | so fabric referencia fingerprint | **sem consumidor real** | nomear doc-only |
| Recovery | S (collect) | S (collect) | S (collect) | S (collect) | taxonomia FailureKinds | `collectors/recover.py` | — | pipelines nao coletam live | documentar taxonomia |
| Env fingerprint | H | H | H | H | `case_meta.environment_fingerprint` | por pipeline | — | fechada W1: `azure/fingerprint.py` | — |
| Eval lab | H | H | H | H | `evals/convergence/` | runner compartilhado | cases por vertical | fechada W1: 20/20 celulas | — |

## Divergencias deliberadas (nao forcar identidade, §10)

- Nomes de graph keys por vertical (`access_graph` vs `fabric_graph`…)
  — o `graph` generico acompanha todos; alias nao e necessario.
- `failure_layer`, `delivery`, `readiness`, `per_asset` sao campos
  semanticos por dominio — corretos.
