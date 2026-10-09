# Documentação — Spark Forge Azure

Mapa da documentação do repositório. O contrato de trabalho de qualquer agente
é a raiz: `AGENTS.md` (CLAUDE.md aponta para lá).

## Começar

| Doc | O que é |
|---|---|
| `README.md` (raiz) | Identidade, invariants, entry points |
| `docs/product/PRODUCT_DEFINITION.md` | Produto, escopo v0.1.0, DoD |
| `docs/ROADMAP.md` | Ondas W0–W15 + estado medido da entrega |
| `CONTRIBUTING.md` | Fluxo SDD, gates de verificação, o que não entra |

## Referência

| Doc | Cobre |
|---|---|
| `docs/reference/knowledge-packs.md` | Packs de knowledge por vertical + escopo por failure_layer |
| `docs/reference/cli.md` | Toda a CLI `sparkforge-azure`: verbos, flags, saída JSON, exit codes |
| `docs/reference/mcp-tools.md` | As tools `sfa_*` (fonte canônica: `docs/surface.lock.json`): risco, parâmetros, envelope |
| `docs/reference/skills.md` | Catálogo gerado das 22 skills (contrato v1): scope, triggers, handoffs, evals por kind — `gen_skills_doc.py` |

## Arquitetura

| Doc | Cobre |
|---|---|
| `docs/architecture/adr/ADR-0001-architecture.md` | Camadas L0–L8, cortes de aresta, facts→rules→findings |
| `docs/architecture/adr/ADR-0002-python-package-name.md` | Por que `sparkforge_azure` |
| `docs/architecture/adr/ADR-0003-two-verticals-one-core.md` | Databricks + Fabric sobre o mesmo núcleo; docs como superfície |
| `docs/architecture/VERTICAL_CONTRACT.md` | Os 12 pontos de contato + invariantes de todo vertical profundo |
| `docs/architecture/MODULE-MAP.md` | Cada pacote `sparkforge_azure/*` em uma linha, por camada |
| `docs/architecture/AWS_TO_AZURE_PORTABILITY_MATRIX.md` | O que veio do AWS e por quê |
| `docs/architecture/AZURE_CAPABILITY_MAP.md` | Capabilities Azure vs. mecanismo |
| `docs/architecture/GRAPHFY.md` | O grafo semântico/de workspace |
| `docs/architecture/SHARED-PRIMITIVES.md` | Primitivas compartilhadas multi-forge |
| `docs/architecture/MULTI-FORGE-INSTALLATION.md` | Convivência AWS + Azure na mesma máquina |
| `parity.yaml` (raiz) | Status real por subsistema + hosts (gerado, `scripts/gen_parity.py`) |
| `manifest.json` (raiz) | Capabilities publicadas (gerado) |
| `docs/architecture/evidence/` | `aws_audit.json`, `provenance.json`, `dropped_aws_tests.json` |

## Portabilidade

| Doc | Cobre |
|---|---|
| `docs/portability/PORTABILITY_AUDIT.md` | Auditoria API Forge/AWS vs Azure: paridade, gaps, classes COPY_SAFE/ADAPT/REFERENCE_ONLY/DO_NOT_PORT |
| `docs/portability/PORTABLE_DISTRIBUTION.md` | Lifecycle portável: inspect/init/status/doctor/detach, identidade relocável, ledger gerenciado, config com precedência |

## Operação

| Doc | Cobre |
|---|---|
| `docs/operations/runbook.md` | Gates de verificação, regeneração de locks, manutenção |
| `docs/agentops.md` | Spans/runs gravadas: `agentops runs/inspect/timeline/critical-path` |
| `docs/agentic/AGENT_INVENTORY.md` | Status por agent da frota (gerado, `scripts/gen_agent_inventory.py`) |
| `docs/agentic/MATURITY_MAP.md` | Auditoria seção→artefato do prompt de maturidade (autoral) |
| `docs/agentic/RUNTIME_EXECUTION_AUDIT.md` | Classificação §5-9: cada runtime DECLARED→…→EVALUATED com prova |
| `docs/agentic/RUNTIME_ADAPTERS.md` | Adapter boundary, registry, vocabulários fechados, fallback §77 |
| `docs/agentic/HOST_EXECUTION.md` | Fluxo canônico §24, handoff §40-42, fingerprint/resume §46-48 |
| `docs/agentic/EMPIRICAL_AGENT_VALUE.md` | Harness A/B §50-75, value vector, necessity §59 |
| `docs/agentic/AGENTIC_ARCHITECTURE_FREEZE.md` | Freeze gate §179-188: decisão `candidate` + bloqueios |
| `docs/agentic/RUNTIME_EXECUTION_OUTCOME.md` | Outcome brief §190-191 do cycle 9 |
| `docs/reference/agents.md` | Catálogo gerado dos 40 agents (contrato v2): kind, domain, autonomy, evals — `gen_agents_doc.py` |
| `docs/tokensave/benchmark.md` | Benchmark reproduzível TokenSave (bytes evitados por profile) |
| `docs/parity/AWS_AZURE_PARITY_AUDIT.md` | Auditoria capability-a-capability AWS↔Azure + wave log do ciclo 11 |
| `docs/parity/ECONOMY_PARITY.md` | Comparativo de economia mecanismo-a-mecanismo (§135-136) com números medidos |
| `docs/parity/AZURE_ARCHITECTURE_FREEZE_READINESS.md` | Avaliação das 8 condições §133 de freeze — veredito `ready` com provas |
| `docs/parity/AWS_AZURE_PARITY_OUTCOME.md` | Outcome machine-readable do ciclo de paridade (§213-214) |

## Labs executáveis

| Doc | Cobre |
|---|---|
| `docs/labs/access.md` | 10 cenários UC/ADLS (`diagnose --suite`) + security/taint |
| `docs/labs/fabric.md` | 16 cenários Fabric (`diagnose fabric --suite`) + coletor live opt-in |
| `docs/labs/stream.md` | 22 cenários Streaming/RTI (`diagnose stream --suite`) + correctness semantics |
| `docs/labs/migration.md` | 22 cenários de migração ADF/Synapse→Fabric (`migration assess --suite`) |

## Ciclos de entrega

| Doc | Cobre |
|---|---|
| `docs/cycle2/DESIGN.md` | Design do vertical UC/ADLS (decisões, alternativas) |
| `docs/cycle2/CLOSURE.md` | Closure auditado do Cycle 2 (SHAs, gates, recusas) |
| `docs/cycle2/OUTCOME_BRIEF.md` | Resultado medido do vertical UC/ADLS |
| `docs/cycle3/OUTCOME_BRIEF.md` | Resultado medido do vertical Microsoft Fabric |
| `docs/cycle4/OUTCOME_BRIEF.md` | Resultado medido do vertical Streaming/RTI |
| `docs/cycle5/OUTCOME_BRIEF.md` | Resultado medido do vertical de migração ADF/Synapse→Fabric |
| `docs/cycle6/OUTCOME_BRIEF.md` | Resultado do hardening do runtime agêntico (contrato v2, spawn gate, teams, spans, labs) |
| `docs/cycle6/CONVERGENCE_AUDIT.md` | Auditoria Wave 0 do ciclo de convergência: o que existe, o que está no hot path, divergências medidas |
| `docs/cycle6/CROSS_VERTICAL_MATRIX.md` | Matriz capability × 4 verticais (contrato compartilhado vs. especialização) |
| `docs/cycle6/WAVE_EVIDENCE.md` | Evidência nomeada por wave do prompt de convergência + gaps honestos |
| `docs/cycle6/ARCHITECTURE_FREEZE_READINESS.md` | Avaliação dos 14 candidatos de freeze §96-97 + decisão |
| `docs/architecture/DATABRICKS_FABRIC_COMMON_PRIMITIVES.md` | Fronteira comum vs. específica dos dois verticais |
| `docs/research/azure_sources_2026-10-06.md` | Fontes oficiais usadas na pesquisa dos verticais |

## Domínio

| Doc | Cobre |
|---|---|
| `knowledge/INDEX.md` | Índice do corpus (gerado) |
| `knowledge/sources.lock.json` | Fonte + freshness de cada entrada |
| `rules/catalog/*.yaml` | Catálogo de regras + roteamento |
| `skills/<nome>/SKILL.md` | 22 skills (contrato v1) |
| `agents/<nome>.md` | 38 manifests de agente |

## Harness / Segurança de conteúdo

| Doc | Cobre |
|---|---|
| `docs/harness/UNTRUSTED-CONTENT.md` | Texto de artefato é dado, nunca autoridade |
| `docs/superpowers/` | Status do plugin superpowers |
| `docs/sdd/` | Migração SDD + eval + archive histórico |

## Locks gerados (não editar à mão)

- `docs/surface.lock.json` — superfície CLI/MCP/skills/knowledge (`check_surface_lock.py`)
- `docs/claims.lock.json` — claims públicos com prova executável (`check_claims.py`)
- `knowledge/INDEX.md`, `knowledge/offline-manifest.json`, `knowledge/sources.lock.json`
- `parity.yaml`, `manifest.json` (`scripts/gen_parity.py`)
