---
sdd: 1
feature: SKILLS_AGENTS_HARDENING
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/SKILLS_AGENTS_HARDENING/explore.md
  sha256: "0d83b789aa28f3a2e350a9b41eac339184908393421a04cd8ba56c3e131cad93"
hypothesis:
  claim: Skills e agents que so citam comandos executaveis (e com sintaxe que a CLI
    aceita) param de gastar tentativas em becos sem saida sem perder a disciplina de
    evidencia que hoje acrescentam
  prediction: no re-run do eval (mesmos 6 casos), with_skill passa a assercao de
    comando inexistente em 6/6 e o tempo medio cai abaixo do baseline atual com
    skill (188 s); assercoes de conteudo continuam passando
  experiment: re-run skills-eval iteration-2 (new skill vs snapshot) + pytest tests/test_skills_agents_hardening.py
acceptance:
- id: AC1
  statement: todo mirror de agent em .claude/agents/custom declara tools sem Write/Edit;
    Bash so quando o manifest tem tool sfa_*
  verified_by:
    kind: test
    ref: tests/test_skills_agents_hardening.py::test_ac1_mirror_declares_host_tools
- id: AC2
  statement: description do mirror de specialist diz quando usar (termos da tabela de
    roteamento) alem da missao
  verified_by:
    kind: test
    ref: tests/test_skills_agents_hardening.py::test_ac2_mirror_description_says_when
- id: AC3
  statement: todo item de does_not de agent e uma negacao (comeca com nao/nunca);
    o validador recusa o contrario
  verified_by:
    kind: test
    ref: tests/test_skills_agents_hardening.py::test_ac3_does_not_is_negation
- id: AC4
  statement: 'sparkforge-azure analyze pyspark, judge e knowledge select existem e
    emitem JSON: facts do arquivo, findings com rule_id e evidence, claims do pack'
  verified_by:
    kind: test
    ref: tests/test_cli_analyze_judge.py::test_ac4_analyze_judge_knowledge_roundtrip
- id: AC5
  statement: tool_ref de CLI e comando citado no corpo de skill resolvem para um
    caminho real da CLI; verbo sem motor so aparece em planned_tool_refs e nunca no
    corpo
  verified_by:
    kind: test
    ref: tests/test_skills_agents_hardening.py::test_ac5_skill_cli_refs_resolve
- id: AC6
  statement: toda linha de comando sparkforge-azure no corpo das skills e aceita pelo
    parser real e todo cenario de lab citado existe
  verified_by:
    kind: test
    ref: tests/test_skills_agents_hardening.py::test_ac6_skill_body_commands_parse
- id: AC7
  statement: analyze-batch-loop e skill de algum agent; o termo de rota generico scan
    nao manda "full table scan" ao purview
  verified_by:
    kind: test
    ref: tests/test_skills_agents_hardening.py::test_ac7_batch_loop_wired_and_scan_not_purview
success:
- id: SC1
  metric: eval with_skill sem tentativa em comando inexistente e tempo medio menor que
    188 s
  source: scratchpad skills-eval/iteration-2/benchmark.json
out_of_scope:
- implementar os 30 analyze <kind> sem extrator (ficam planned_tool_refs)
- expor analyze/judge/knowledge como tool MCP
- mapear model_tier para model do host
- bug do extrator pyspark.join com how posicional (issue separada)
unknowns: []
change_kinds:
- agent_or_skill
- tool_or_verb
---

# Define — SKILLS_AGENTS_HARDENING
