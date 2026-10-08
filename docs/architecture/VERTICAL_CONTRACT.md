# Vertical Contract — como um vertical profundo pluga no núcleo

ADR-0001 define as camadas. Este documento define o **contrato observável** que
todo vertical de domínio (`azure` access, `fabric`, `stream`, `migration`)
cumpre — o padrão repetido nos cycles 2–5, promovido a contrato.

> Regra de ouro: um vertical é um pipeline determinístico **evidence-bound**,
> não uma coleção de checks. Facts → Rules → Findings; ausência de evidência
> é `unresolved`, nunca sucesso implícito.

## Os 12 pontos de contato

| # | Ponto de contato | Onde | Verificado por |
|---|---|---|---|
| 1 | Pacote de domínio com pipeline `extract → assess → report` | `sparkforge_azure/<vertical>/` | `tests/test_<vertical>_*.py` |
| 2 | Facts tipados `<prefix>.*` com provenance | `migration/extract.py` et al. | suite de lab + testes |
| 3 | Redação de segredos no boundary de extração | `collectors.redact` | testes `*redacted*` |
| 4 | Camada de grafo tipada (sem importar o domínio) | `graph/<vertical>.py` + layer em `graph/model.py` | `test_<vertical>_graph.py` |
| 5 | Catálogo de regras `SF-<PREFIX>-*` | `rules/catalog/<vertical>.yaml` | doctor `<vertical>_vertical` |
| 6 | Knowledge packs escopados `vertical: <name>` | `knowledge/packs.yaml` | `test_knowledge_vertical.py` |
| 7 | Rota AgentOps `AGENT-XXX` → specialist com `rule_areas` | `rules/catalog/routing.yaml` + `agents/<spec>.md` | `check_skills_agents.py` |
| 8 | Spans `<vertical>.<stage>` no ledger | pipeline | teste de spans |
| 9 | Verbo(s) CLI | `cli/cmd_<vertical>.py` + `COMMAND_MODULES` | `surface.lock.json` |
| 10 | Tool MCP `sfa_*` (read_only, projeção compacta) | `mcp/` | catálogo + claim |
| 11 | Lab determinístico com oráculo `expect:` | `tests/fixtures/<vertical>/` + `docs/labs/<vertical>.md` | `run_<vertical>_suite` |
| 12 | Doctor check `<vertical>_vertical` | `doctor.py` | `sparkforge-azure doctor` |

E mais, fora do pacote:

- **Arestas de arquitetura declaradas**: `(vertical, azure|findings|agentic|
  facts|graph|rules|observability|knowledgebase|collectors)` e
  `(cli|mcp|doctor, vertical)` em `tests/test_architecture_layers.py`.
- **Skills verticais**: skills do domínio entram em `VERTICAL_SKILLS` com
  evals positive/negative/boundary ancorados no SKILL.md.
- **Claims**: `docs/claims.lock.json` ganha claims executáveis
  (`<vertical>-suite-green`, `<vertical>-mcp-surface`).
- **SDD**: um sub-SDD por área P0 em `docs/sdd/<FEATURE>/` com
  `build_report.md` red→green honesto (red real no commit base).
- **Docs**: entrada em `docs/README.md`, seção medida em `docs/ROADMAP.md`,
  linha em `AZURE_CAPABILITY_MAP.md`, `OUTCOME_BRIEF` do ciclo.

## Invariantes semânticas (todo vertical herda)

1. **Unresolved-first**: ausência de artefato/evidência nunca é `pass`/`READY`.
   O vocabulário de status é fechado e declarado em `<vertical>/model.py`.
2. **Trust**: `instruction_authority=data_only`; conteúdo de artefato é dado,
   nunca instrução; taint `external` preservado.
3. **Offline-first**: o caminho `--bundle` funciona sem credencial; coleta live
   é opt-in, read-only, via `collectors`.
4. **Semântica, não nome**: identidade = ID canônico (ARM/GUID); display name é
   atributo. Referência ausente → `graph.unresolved`, nunca nó inventado.
5. **Evidência oficial ≠ autoridade**: exports de terceiro (assessment etc.)
   são `external evidence` — divergência vira finding de conflito.
6. **Sem equivalência falsa**: "X = Y" entre serviços é candidato mediado por
   evidência, nunca mapeamento cego (invariante 7 do AGENTS.md).

## Referência por vertical

| Vertical | Pacote | Regras | Lab | MCP |
|---|---|---|---|---|
| Access (UC/ADLS) | `azure/` | `SF-ACC-*` | `tests/fixtures/access` (10) | `sfa_diagnose_access` |
| Fabric | `fabric/` | `SF-FAB-*` | `tests/fixtures/fabric` (16) | `sfa_diagnose_fabric` |
| Streaming/RTI | `stream/` | `SF-STR-*`, `SF-RTI-*` | `tests/fixtures/stream` (22) | `sfa_diagnose_stream` |
| Migration | `migration/` | `SF-MIG-*` | `tests/fixtures/migration` (22) | `sfa_assess_migration` |

Adicionar um vertical novo = satisfazer os 12 pontos + invariantes, com SDD
antes do código (red→green) e PR medindo os gates do runbook.
