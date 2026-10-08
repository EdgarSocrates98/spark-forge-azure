# Cycle 2 — outcome brief (prompt 206)

| campo | valor |
|---|---|
| BASE_SHA | `b1caf70280a95479f4dcd9bb98b119b46ce823e5` |
| FINAL_SHA | `15ffb95` (último commit de código; docs deste brief em seguida) |
| branch | `feat/cycle2-evolution` → PR #3 → merge `fe6b8a5` em `main` |
| tests | **2533 passed, 9 skipped** (pytest ~3min, Python 3.12 venv) |
| CI | `NOT_OBSERVED` — quota GitHub indisponível; gates locais verdes |

## Por capability

| capability | estado medido |
|---|---|
| MCP | runtime real (SDK `mcp` 2.3.0), 10 tools, risco declarado, annotations, dispatch com spans; matriz `evals/mcp-conformance/` |
| Databricks vertical | `diagnose --bundle|--suite` — 10/10 cenários, `failure_layer`, `evidence_paths`, receipt por caso |
| Graphfy | `graph/access.py` na resolução (evidence path derivado do grafo), federação por ARM-id com `attr_conflicts`, queries bounded |
| TokenSave | benchmark real: baseline 10415 B; economy 1964 B; balanced/deep 2981 B; `tokens: unresolved` sem provider |
| AgentOps | spans `diagnose.*`, `agentops inspect/timeline/critical-path`, waste patterns, `context_quality`, memory fingerprint, recovery taxonomy + counterfactual |
| Security | taint lab (4 vetores `DATA_ONLY`), redaction na fronteira (SAS/secret/key/bearer/connstring), env-mismatch `SF-ACC-013`, trust floor data_only |
| Claims | 10 claims com prova executável em `docs/claims.lock.json` |
| Surface | 10 MCP tools + CLI estável; `surface.lock.json` verde |

## Status correto por área (prompt 204)

| área | estado |
|---|---|
| Agentic foundation | mature |
| Databricks UC/ADLS access vertical | **deep** (10 cenários + evidence + grafo + agentops) |
| Knowledge packs do vertical | presente, escopo determinístico por failure_layer |
| Fabric / ADF / Synapse / Streaming | foundation (fora do escopo do cycle) |

## Remaining gaps (honestos)

- `live` collectors nunca exercitados contra Azure real neste ciclo —
  SDK paths existem com fallback visível; live runs são Tier 4 opt-in.
- `tokens` permanece `unresolved` — sem provider de billing/tokens
  observado; bytes são a medida honesta hoje.
- Cache live é in-memory por processo; persistência fica fora de escopo
  por decisão (raw export redatado já existe).
- Cross-env cobre divergence entre artefatos do bundle; fingerprint de
  memória cobre reutilização entre ambientes.
- Golden transcripts (Tier 3) não gravados neste ciclo.

## Não-invenções honradas

- Nenhum "suporta Databricks" genérico — claims dizem exatamente o que
  executam (#199).
- CI remoto declarado `NOT_OBSERVED`, não fingido verde (#215).
- Cycle 3 **não** iniciado; candidatos documentados para auditoria (#216-217).
