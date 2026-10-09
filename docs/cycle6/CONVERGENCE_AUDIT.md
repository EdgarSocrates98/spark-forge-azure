# Cycle 6 — Convergence Audit (Wave 0)

`prompt_evo_cycle6.md` §5: antes de qualquer codigo, auditar quais
componentes existem, quais estao no hot path, quais sao duplicados,
medidos, fail-open/closed, e quais nao tem consumidor real.

Medido neste repositorio em `feat/cycle6-convergence` (base
`21ac3e9`, pos-merge do PR #18 de paridade).

## Inventario de componentes por estado

| componente | existe | hot path dos 4 verticais | duplicado | medido | falha | consumidor real |
|---|---|---|---|---|---|---|
| Facts → Rules → Findings | `facts/`, `rules/`, `findings/` | **sim** — os 4 `run_case` | nao | gate recall + fixtures golden | closed (rules_skipped nomeados) | pipelines |
| Graph (Graphfy) | `graph/` 17 modulos | **sim** — `*_graph` em todo resultado | nao | testes de grafo por vertical | closed | pipelines + MCP `sfa_graph_*` |
| Knowledge compiler | `knowledgebase/` | **sim** — `knowledge` em todo resultado | nao | knowledge-check claim | closed | pipelines |
| AgentOps | `observability/` + `agentic/spans.py` | **sim** — `stages`/`overhead` em todo resultado | nao | test_agentops_vertical | closed | pipelines |
| Receipt | `receipt/`, `decision/receipts.py` | **sim** — `receipt` + `evidence_paths` | nao | verify claims | closed | pipelines |
| Trust (DATA_ONLY/taint) | `agentic/trust.py` | **sim** — `taint`/`trust` em todo resultado | nao | redteam tests | closed | pipelines + handoffs |
| Upstream facts | `adapters/upstream.py` | **sim** — `upstream.json` nos 4 casefiles | nao | test_upstream_facts (11) | closed (bounds + forbidden keys) | pipelines |
| Context Gateway | `context/` 15 modulos | **nao** — pipelines sao deterministicos; gateway serve consumidores LLM | nao | token_benchmark 45/45, recall gate | closed | evals + agentic |
| TokenSave | CLI `tokensave` + MCP | **nao** — idem gateway (superficie de contexto, nao de diagnostico) | nao | tokensave-benchmark claim | closed | CLI/MCP |
| Code Intelligence | `codeintel/` 18 modulos | **nao** nos pipelines — serve o gateway | nao | suite codeintel inteira | closed | gateway |
| Memory | `azure/memory.py` | **nao** — `record_access_case` nao e chamada por pipeline nem MCP | nao | test_runtime_convergence_memory_v3 | — | **sem consumidor real** |
| Recovery taxonomy | `collectors/recover.py`, `agentic/stop.py`, runtimes `FailureKinds` | parcial — so `cmd_collect` usa `collect_with_recovery`; pipelines nao coletam live | nao | testes de recovery | closed | CLI collect |
| Evaluation plane | `evals/` 18 modulos | n/a (fora do hot path por design) | nao | self-tested | closed | gates |
| Agent runtime | `agentic/runtimes/` | n/a — sobe por `agents execute` | nao | freeze 6/6, host proof | closed (fail-closed) | `claude_code` provado |

## Achados (medidos, nao cosmeticos)

1. **Convergencia estrutural dos recibos e real.** Os 4 `run_case`
   devolvem o mesmo nucleo: `case`, `case_meta`, `facts`, `findings`,
   `rules_skipped`, `unresolved`, `knowledge`, `graph` (+ graph tipado por
   vertical), `evidence_paths`, `trust`, `taint`, `stages`,
   `overhead`, `receipt`, `status`, `operation`.
2. **`environment_fingerprint` existia em fabric/stream/migration e
   faltava em databricks — fechado na Wave 1** via
   `azure/fingerprint.py` (`case_meta.environment_fingerprint`, mesma
   posicao semantica dos demais). `evidence_paths` faltava em migration
   — fechado na Wave 1 via `migration._evidence_paths` (finding ->
   facts -> arquivo de proveniencia). Validado por
   `evals/convergence/runner.py`: 20/20 celulas (4 casos x 5 profiles).
3. **Memory nao tem consumidor real.** `azure/memory.py` define
   `record_access_case`/`env_fingerprint` e nenhum pipeline, MCP tool ou
   CLI os invoca. Candidato a `doc-only`: declarar como tal ou ligar a um
   consumidor — nao fingir que esta no hot path.
4. **Context Gateway / TokenSave / CodeIntel sao superficie de consumo
   LLM**, nao parte do pipeline deterministico. Isso e o desenho (§10:
   convergir contratos, nao forcar implementacao identica) — mas ficava
   implicito; agora esta medido.
5. **Recovery nos pipelines e nominalmente ausente**: pipelines nao
   fazem I/O de nuvem (fail-closed por construcao); a taxonomia vive em
   `collectors/recover.py` e `agentic/runtimes` (`FailureKinds`). Sem
   gap de correcao; gap de DOCUMENTACAO — a taxonomia precisa ser nomeada
   igual nos dois lugares.

## Conclusao da Wave 0

Nenhum fork arquitetural acidental entre verticais. Os unicos achados de
codigo sao `environment_fingerprint` ausente em databricks e `memory` sem
consumidor — ambos pequenos, ambos fechados neste ciclo ou nomeados como
`doc-only` deliberado.
