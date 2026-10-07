---
sdd: 1
feature: SDD_MIGRATION
phase: define
profile: dev
status: done
hypothesis:
  claim: o processo AgentSpec pode ser trocado pelo SDD sem apagar a historia
  prediction: docs de entrada apontam o SDD e o historico fica arquivado
  experiment: conferir settings, arquivo morto e referencias nos documentos
acceptance:
  - id: AC1
    statement: plugin agentspec desligado em .claude/settings.json
    verified_by:
      kind: test
      ref: tests/test_sdd_migration.py::test_agentspec_desligado_no_projeto
  - id: AC2
    statement: historico agentspec arquivado em docs/sdd/archive/agentspec/ e .claude/sdd/ fora do git
    verified_by:
      kind: test
      ref: tests/test_sdd_migration.py::test_historico_agentspec_arquivado
  - id: AC3
    statement: superpowers congelado com README apontando docs/sdd/
    verified_by:
      kind: test
      ref: tests/test_sdd_migration.py::test_superpowers_congelado
  - id: AC4
    statement: CLAUDE.md, AGENTS.md e CONTRIBUTING.md citam sdd-define e o comando do gate
    verified_by:
      kind: test
      ref: tests/test_sdd_migration.py::test_documentos_de_entrada_apontam_o_sdd
  - id: AC5
    statement: README.md cita sdd-define e o journal local fica no .gitignore
    verified_by:
      kind: test
      ref: tests/test_sdd_migration.py::test_readme_e_journal
success:
  - id: SC1
    metric: zero referencias ao fluxo SDD em .claude/sdd/ nos documentos de entrada
    source: tests/test_sdd_migration.py
out_of_scope:
  - remover skills locais do operador em ~/.claude (estado da maquina, nao do repo)
change_kinds: []
---

# SDD_MIGRATION — define

Migrar processo sem guardar historia e reescrever o passado. O AgentSpec sai de
cena com o historico arquivado em `docs/sdd/archive/agentspec/`, o plugin
desligado por nome e os documentos de entrada apontando o fluxo novo —
`sdd-define` para abrir feature, `sparkforge sdd check` (no sibling AWS) e
`sparkforge-azure sdd check` aqui para o gate.
