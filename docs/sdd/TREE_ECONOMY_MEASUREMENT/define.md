---
sdd: 1
feature: TREE_ECONOMY_MEASUREMENT
phase: define
profile: dev
status: done
hypothesis:
  claim: 'o gate de recall/economia fica unresolved porque o corpus de
    fixture (1433 B) nao paga o envelope fixo do pack (747 B/chamada). O
    proprio gate nomeia a medida que destrava: a mesma medicao sobre a
    arvore do repositorio — 380 modulos reais'
  prediction: 'gold set derivado de `__all__` ∩ defs do proprio modulo
    produz ~225 perguntas nominais sobre corpus real; a medicao expoe a
    razao de economia com denominador (pack vs arquivos vs grep) e
    revela o gap de retrieval de simbolo composto'
  experiment: python scripts/check_recall_economy.py
acceptance:
- id: AC1
  statement: 'derivar_goldset_arvore() produz pares (arquivo, simbolo)
    apenas de nomes presentes em `__all__` E definidos como def/class
    no mesmo modulo — nada escolhido a mao, nada re-exportado'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_tree_gold_set_is_derived_and_nonempty
- id: AC2
  statement: 'medir_arvore() indexa a arvore UMA vez e mede todas as
    perguntas sobre esse indice — sem escrever estado no repo'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_tree_measurement_has_denominators
- id: AC3
  statement: 'o bloco economia_arvore do gate publica razao real
    (contra_arquivos > 1) quando o corpus excede o envelope — encerrando
    o unresolved NOMEADO, nao apagado'
  verified_by:
    kind: test
    ref: tests/test_recall_economy_gate.py::test_tree_economy_is_measured
- id: AC4
  statement: 'escore de simbolo composto: quem pede `run_case` recebe
    `run_case` — tokens do nome como fatia contigua dos literais, OU
    igualdade direta do identificador composto quando stopword quebra a
    fatia (`impact_for` → literais `[impact]`), sem ecoar identificador
    cru no pack publicado'
  verified_by:
    kind: test
    ref: tests/test_codeintel_context.py::test_o_texto_da_tarefa_nao_e_ecoado
success:
- id: SC1
  metric: 'gate verde com economia_arvore medida; recall nominal da
    arvore reportado; nenhum identificador cru em expansao.literais'
  source: python scripts/check_recall_economy.py --json
out_of_scope:
- 'recall conceitual na arvore (nao ha titulo de regra para perguntar;
  inventar mediria a escrita, nao o pack)'
- 'ambiguidade de mesmo-nome entre modulos (4 collectors definem
  collect_live — miss honesta nomeada, nao defeito)'
unknowns: []
change_kinds:
- fixture_corpus
---

# Define — TREE_ECONOMY_MEASUREMENT

O gate de economia (W2 do ciclo 11) reporta `unresolved` com a medida de
destravamento nomeada: corpus maior que o envelope, ou a mesma medicao
sobre a arvore do repositorio. Esta feature executa a segunda opcao.

Dois artefatos novos:

1. `goldset.derivar_goldset_arvore()` — gold set derivado de `__all__`
   intersectado com `def`/`class` do proprio modulo. A fonte de verdade
   e a superficie publica declarada no codigo, nao escolha editorial.
2. `recall.medir_arvore(raiz, simbolos)` — um indice compartilhado para
   N perguntas (indexar por pergunta inflaria 225 indexacoes iguais).

A medicao expôs defeito real de retrieval, em duas iteracoes medidas:

1. `exact_name` comparava o nome normalizado inteiro contra literais
   quebrados — `run_case` nunca casava com `{run, case}` (209/225 →
   220/225). Correcao: fatia contigua de tokens + frase FTS por
   identificador composto, via `_identificadores(tarefa)` — buscado,
   nunca publicado em `expansao.literais`.
2. Stopword no meio do nome quebrava a fatia — `impact_for` expande para
   `[impact]` porque `for` e stopword, e `[impact, for]` nao e fatia de
   `[impact]`; o proprio `impact` vencia por `nome in literais`
   (220/225 → 224/226). Correcao: `escore(..., identificadores=)` casa o
   nome normalizado contra o identificador composto da pergunta —
   igualdade no escore, nao na expansao publicada.

Residuais nomeados e mantidos: `codeintel/extract.py::No` (stopword
integra — pergunta filtrada inteira) e `collectors/unity_catalog.py::
collect_live` (ambiguo — 4 collectors definem o mesmo nome).
