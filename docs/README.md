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
| `docs/reference/cli.md` | Toda a CLI `sparkforge-azure`: verbos, flags, saída JSON, exit codes |
| `docs/reference/mcp-tools.md` | As tools `sfa_*` (fonte canônica: `docs/surface.lock.json`): risco, parâmetros, envelope |

## Arquitetura

| Doc | Cobre |
|---|---|
| `docs/architecture/adr/ADR-0001-architecture.md` | Camadas L0–L8, cortes de aresta, facts→rules→findings |
| `docs/architecture/adr/ADR-0002-python-package-name.md` | Por que `sparkforge_azure` |
| `docs/architecture/adr/ADR-0003-two-verticals-one-core.md` | Databricks + Fabric sobre o mesmo núcleo; docs como superfície |
| `docs/architecture/MODULE-MAP.md` | Cada pacote `sparkforge_azure/*` em uma linha, por camada |
| `docs/architecture/AWS_TO_AZURE_PORTABILITY_MATRIX.md` | O que veio do AWS e por quê |
| `docs/architecture/AZURE_CAPABILITY_MAP.md` | Capabilities Azure vs. mecanismo |
| `docs/architecture/GRAPHFY.md` | O grafo semântico/de workspace |
| `docs/architecture/SHARED-PRIMITIVES.md` | Primitivas compartilhadas multi-forge |
| `docs/architecture/MULTI-FORGE-INSTALLATION.md` | Convivência AWS + Azure na mesma máquina |
| `parity.yaml` (raiz) | Status real por subsistema + hosts (gerado, `scripts/gen_parity.py`) |
| `manifest.json` (raiz) | Capabilities publicadas (gerado) |
| `docs/architecture/evidence/` | `aws_audit.json`, `provenance.json`, `dropped_aws_tests.json` |

## Operação

| Doc | Cobre |
|---|---|
| `docs/operations/runbook.md` | Gates de verificação, regeneração de locks, manutenção |
| `docs/agentops.md` | Spans/runs gravadas: `agentops runs/inspect/timeline/critical-path` |

## Labs executáveis

| Doc | Cobre |
|---|---|
| `docs/labs/access.md` | 10 cenários UC/ADLS (`diagnose --suite`) + security/taint |
| `docs/labs/fabric.md` | 16 cenários Fabric (`diagnose fabric --suite`) + coletor live opt-in |
| `docs/labs/stream.md` | 22 cenários Streaming/RTI (`diagnose stream --suite`) + correctness semantics |

## Ciclos de entrega

| Doc | Cobre |
|---|---|
| `docs/cycle2/CLOSURE.md` | Closure auditado do Cycle 2 (SHAs, gates, recusas) |
| `docs/cycle2/OUTCOME_BRIEF.md` | Resultado medido do vertical UC/ADLS |
| `docs/cycle3/OUTCOME_BRIEF.md` | Resultado medido do vertical Microsoft Fabric |
| `docs/cycle4/OUTCOME_BRIEF.md` | Resultado medido do vertical Streaming/RTI |
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
