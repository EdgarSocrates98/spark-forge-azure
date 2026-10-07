---
sdd: 1
feature: SDD_EVAL
phase: define
profile: dev
status: done
hypothesis:
  claim: a suite agentica sobre specs deriva todas as respostas do gate do SDD
  prediction: cada pergunta tem resposta unica recomputada por check/status
  experiment: recomputar o gabarito rodando o gate sobre as cinco fixtures
acceptance:
  - id: AC1
    statement: cinco repositorios sinteticos em fixtures/sdd/, cada um quebrando no maximo uma coisa
    verified_by:
      kind: test
      ref: tests/test_fixtures_golden_sdd.py::test_o_corpus_tem_os_cinco_casos
  - id: AC2
    statement: cada caso devolve exatamente a recusa para a qual foi montado, e nenhum unresolved
    verified_by:
      kind: test
      ref: tests/test_fixtures_golden_sdd.py::test_cada_caso_da_so_a_recusa_que_foi_montada
  - id: AC3
    statement: o limpo chega a ship/done
    verified_by:
      kind: test
      ref: tests/test_fixtures_golden_sdd.py::test_o_caso_limpo_esta_no_ship
  - id: AC4
    statement: o gabarito da suite e recomputado pelo gate, nunca escrito a mao
    verified_by:
      kind: test
      ref: tests/test_sdd_eval_suite.py::test_gabarito_recomputado_pelo_gate
  - id: AC5
    statement: baselines gravados pontuaram contra o sha256 desta suite, pergunta por pergunta
    verified_by:
      kind: test
      ref: tests/test_sdd_eval_suite.py::test_suite_carrega_e_exige_as_tools
  - id: AC6
    statement: fixtures/sdd/ fora da conversao de quebra de linha, com a nota do text_sha256
    verified_by:
      kind: test
      ref: tests/test_sdd_eval_suite.py::test_fixtures_sem_conversao_de_quebra
success:
  - id: SC1
    metric: seis perguntas da suite respondidas por um valor derivado do gate
    source: tests/test_sdd_eval_suite.py
out_of_scope:
  - execucao de agente de verdade no CI (o runner entrega workspace + contrato)
change_kinds: []
---

# SDD_EVAL — define

Uma suite agentica so mede o que o gate mede: se a resposta certa exigir
interpretacao, o gabarito vira opiniao. Por isso cada fixture quebra uma coisa
so e cada pergunta pede um valor so — `code`, `path`, id ou fase — recomputado
por `check`/`status` em `tests/test_sdd_eval_suite.py`.
