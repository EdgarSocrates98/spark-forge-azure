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

- Suite: **2538 testes verdes** (9 skipped), `ruff` limpo, `check_surface_lock`,
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

## Estado medido — cycle 2 (vertical de acesso UC/ADLS)

Medido sobre `feat/cycle2-evolution`:

- Vertical de acesso executável: `sparkforge-azure diagnose --bundle|--suite`
  cobre 10 cenários determinísticos (UC→RBAC→ACL→rede→binding→location→
  bypass→runtime→delta→abstain) com `failure_layer`, `evidence_paths`,
  `access_graph`, `context_quality`, `trust` (DATA_ONLY), `knowledge`
  escopado e receipt por caso.
- MCP runtime real: `mcp` SDK Server sobre o registry `sfa_*` (10 tools,
  risco declarado, annotations derivadas, dispatch com spans AgentOps).
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
- Suite: **2538 testes verdes** (9 skipped).
