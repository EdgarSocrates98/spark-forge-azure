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
| `docs/reference/skills.md` | Catálogo gerado das 23 skills (contrato v1): scope, triggers, handoffs, evals por kind — `gen_skills_doc.py` |
| `docs/reference/commands.md` | Referência gerada por comando (`doc_inventory`+`doc_reference`): rationale por grupo |

## Instalação

| Doc | Cobre |
|---|---|
| `docs/installation/quickstart.md` | Quickstart pt-BR: install → doctor → primeiro analyze |
| `docs/installation/quickstart.en.md` | Mesmo quickstart em EN |
| `docs/installation/account-installation.md` | Runtime account-scoped: venv central, editable CLI e variáveis persistentes |
| `docs/installation/global-installation.md` | Instalação global (escopo user): quando usar, e o que muda |
| `docs/installation/workspace-installation.md` | Instalação em workspace multi-projeto |
| `docs/installation/portable-installation.md` | Instalação portável sem checkout |
| `docs/installation/mcp.md` | O servidor MCP: `mcp serve`, handshake, configuração por host |
| `docs/installation/claude-code.md` | Integração com Claude Code: escopo, mirrors, aprovação |
| `docs/installation/devin-cli.md` | Integração com Devin CLI: skills/agents nativas |
| `docs/installation/codex-cli.md` | Integração com Codex CLI — MCP só em escopo user (limitação do host) |
| `docs/installation/copilot-cli.md` | Integração com GitHub Copilot CLI |
| `docs/installation/update-and-repair.md` | `install update|repair`: drift → correção |
| `docs/installation/uninstall.md` | `install uninstall`: detach limpo e `--purge` |
| `docs/installation/troubleshooting.md` | Falhas comuns de instalação e unlock |
| `docs/installation/troubleshooting.en.md` | Mesmo troubleshooting em EN |

## Aprendizado

| Doc | Cobre |
|---|---|
| `docs/tutorials/first-run.md` | Tutorial: primeira execução real ponta a ponta |
| `docs/learn/recipes/doctor.md` | Receita: "minha instalação está íntegra?" |
| `docs/learn/recipes/analyze-pyspark.md` | Receita: facts determinísticos de código PySpark |
| `docs/learn/recipes/migration-assessment.md` | Receita: assessment ADF/Synapse → Fabric |
| `docs/learn/recipes/instalacao.md` | Receita: instalar o forge no projeto (scopes, hosts, recibo) |
| `docs/learn/recipes/primeiro-uso.md` | Receita: menor caminho real (install→doctor→analyze→judge) |
| `docs/learn/recipes/analise-azure.md` | Receita: diagnóstico de acesso multicamada (UC/RBAC/ACL/rede) |
| `docs/learn/recipes/fabric.md` | Receita: vertical Fabric (workspace/OneLake/shortcut/capacity) |
| `docs/learn/recipes/adf.md` | Receita: Azure Data Factory (inventory/assess de migração) |
| `docs/learn/recipes/synapse.md` | Receita: Synapse (pools, pipelines, migração p/ Fabric) |
| `docs/learn/recipes/streaming.md` | Receita: Event Hubs + Structured Streaming + Fabric RTI |
| `docs/learn/recipes/usar-agents.md` | Receita: frota de 40 agents — list/inspect/route/execute |
| `docs/learn/recipes/usar-skills.md` | Receita: as 23 skills e o contrato de fronteira |
| `docs/learn/recipes/verificar-mcp.md` | Receita: handshake MCP real + painel `ai` |
| `docs/learn/recipes/graphfy.md` | Receita: `graph build/query/impact/view/ui` (ForgeGraphView/v1) |
| `docs/learn/recipes/economia.md` | Receita: tokensave L0–L6, bytes medidos vs tokens |
| `docs/learn/recipes/abrir-host.md` | Receita: `sparkforge-azure ai` — medir e abrir o host |

## Experiência

| Doc | Cobre |
|---|---|
| `docs/experience/interactive-cli.md` | CLI interativo: home, navegação, comportamento sem TTY |
| `docs/experience/installation-wizard.md` | Wizard de instalação guiada |
| `docs/experience/automation-mode.md` | Modo automação: saída JSON, flags não-interativas |
| `docs/experience/themes.md` | Temas e identidade visual da TUI |
| `docs/experience/accessibility.md` | Acessibilidade da interface |
| `docs/economy.md` | Economia de tokens e contexto: o que é medido vs. estimado |
| `docs/experience/fase3-report.md` | FASE 3 — fechamento: host experience `ai`/`sfa_ai`, E2E instalado, gates |
| `docs/reports/experience-3.md` | Forge Experience 3.0 — relatório da onda de UX |

## Engineering excellence

| Doc | Cobre |
|---|---|
| `docs/engineering-excellence/context-and-planning.md` | Context pointers, bounded context, handoff e planejamento proporcional |

## Knowledge program

| Doc | Cobre |
|---|---|
| `docs/knowledge-program/final-report.md` | Relatório final do programa de knowledge |
| `docs/knowledge-program/classification-report.md` | Classificação do corpus |
| `docs/knowledge-program/documentation-quality-report.md` | Qualidade da documentação medida |
| `docs/knowledge-program/broken-link-report.md` | Links quebrados detectados |
| `docs/knowledge-program/duplicate-content-report.md` | Conteúdo duplicado detectado |
| `docs/knowledge-program/obsolete-document-report.md` | Documentos obsoletos detectados |
| `docs/knowledge-program/command-drift-report.md` | Drift doc↔comando |
| `docs/knowledge-program/tutorial-coverage-report.md` | Cobertura de tutoriais |

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
| `docs/portability/WORKSPACES.md` | ForgeWorkspace: modelo, manifesto, discover/init/add/remove/status, roles, arestas, ciclos, locality |
| `docs/portability/CONTEXT_RESOLUTION.md` | `context resolve`: scopes target/direct/transitive/all, TokenSave por projeto confinado, recibo §58 com bytes |
| `docs/portability/HOST_INTEGRATION.md` | Hosts: `.mcp.json`, blocos gerenciados em AGENTS.md/CLAUDE.md, mirrors opt-in, detecção sem probing |
| `docs/portability/DETACH.md` | Detach/reattach: ledger-driven, preserve-por-padrão, purge granular, dry-run, decisão `repair` |
| `docs/portability/PORTABILITY_OUTCOME.md` | Outcome brief §200–§204: scorecard PROVEN/PARTIAL/DEFERRED + parity final vs API Forge/AWS |
| `docs/portability/TROUBLESHOOTING.md` | Glossário de recusas do lifecycle: cada `kind` (vocabulário fechado), causa típica e `unlock` — padrões de sintoma e diagnóstico rápido |
| `docs/CURRENT_STATE.md` | Estado medido atual da `main` (gerado por `scripts/gen_current_state.py`): SHA, testes, claims, skills, agents, tools, portabilidade, freeze |
| `docs/guides/SPARKFORGE_AZURE_PORTABLE.md` | Quickstart portável (EN): install→init→workspace→resolve→detach sem checkout |
| `docs/guides/SPARKFORGE_AZURE_PORTABLE.pt-BR.md` | Quickstart portável (pt-BR): mesmo ciclo, traduzido |

## Operação

| Doc | Cobre |
|---|---|
| `docs/operations/runbook.md` | Gates de verificação, regeneração de locks, manutenção |
| `docs/releasing/pypi-patch-plan.md` | Plano de patch PyPI c11.2 (metadata, sdist, provenance) |
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
| `docs/evals-taxonomy.md` | Inventário §7.1 classificado das 9 suites de evals + ops §7.2 + postura §7.3 (`sparkforge-azure evals`) |
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
| `docs/audits/FORGE_CONTEXT_BASELINE.md` | Baseline auditado do ciclo Install 2.0 (install/context/distribution; evidência de wheel PyPI 0.1.6) |
| `docs/audits/FORGE_CONTEXT_FINAL_HOMOLOGATION.md` | Homologação final do ciclo Install 2.0 (§12.6: SHAs, PRs, testes, matriz PyPI, gaps restantes) |
| `docs/install/DISTRIBUTION_PARITY.md` | Matriz de paridade §8.5: checkout vs wheel local vs PyPI publicado |

## Domínio

| Doc | Cobre |
|---|---|
| `knowledge/INDEX.md` | Índice do corpus (gerado) |
| `knowledge/sources.lock.json` | Fonte + freshness de cada entrada |
| `rules/catalog/*.yaml` | Catálogo de regras + roteamento |
| `skills/<nome>/SKILL.md` | 23 skills (contrato v1) |
| `agents/<nome>.md` | 38 manifests de agente |

## Harness / Segurança de conteúdo

| Doc | Cobre |
|---|---|
| `docs/harness/UNTRUSTED-CONTENT.md` | Texto de artefato é dado, nunca autoridade |
| `docs/superpowers/` | Status do plugin superpowers |
| `docs/sdd/` | Migração SDD + eval + archive histórico |

## Locks gerados (não editar à mão)

- `docs/INDEX.md` — inventário completo de docs (`doc_index.py` via `regen_docs.py`)
- `docs/surface.lock.json` — superfície CLI/MCP/skills/knowledge (`check_surface_lock.py`)
- `docs/claims.lock.json` — claims públicos com prova executável (`check_claims.py`)
- `knowledge/INDEX.md`, `knowledge/offline-manifest.json`, `knowledge/sources.lock.json`
- `parity.yaml`, `manifest.json` (`scripts/gen_parity.py`)
