---
sdd: 1
feature: TREE_ECONOMY_MEASUREMENT
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/TREE_ECONOMY_MEASUREMENT/define.md
  sha256: "90cfdc1096a38633609f04883183bc813d47ff3149f2393ea33670f30f1978e7"
files:
- path: sparkforge_azure/economy/goldset.py
  action: modify
  reason: derivar_goldset_arvore() — pares (arquivo_rel, simbolo) via
    ast.__all__ ∩ defs do modulo
- path: sparkforge_azure/economy/recall.py
  action: modify
  reason: medir_arvore() — indice unico compartilhado, eixo nominal,
    mesmos campos de bytes de medir()
- path: sparkforge_azure/codeintel/ranking.py
  action: modify
  reason: escore() — exact_name por fatia contigua de tokens do nome OU
    por igualdade com identificador composto (kwarg `identificadores`);
    _contido_adjacente(); NOTA documentada sobre identificador cru nao
    entrar em literais (echo da pergunta e proibido)
- path: sparkforge_azure/codeintel/context.py
  action: modify
  reason: montar() — _identificadores(tarefa) alimenta a busca de frase
    FTS em _candidatos() e o kwarg `identificadores` de escore()
- path: scripts/check_recall_economy.py
  action: modify
  reason: bloco economia_arvore — razao medida com denominador
- path: tests/test_recall_economy_gate.py
  action: modify
  reason: AC1-AC3 — gold set derivado, denominadores, razao medida
decisions:
- id: D1
  choice: gold set de arvore derivado de __all__ ∩ defs — superficie
    publica declarada versionada, nao lista escolhida a mao
  rejected:
  - amostra aleatoria de simbolos — nao e reproduzivel nem defensavel
  - todos os simbolos de todos os modulos — 5000+ perguntas, medicao lenta
  rollback: voltar ao gold set de fixtures apenas
- id: D2
  choice: exact_name por _contido_adjacente(tokens_do_nome, literais)
    OU nome in {_normalizar(i) for i in identificadores} — o
    identificador composto chega ao escore como parametro, nao como
    literal publicado; a frase FTS em _candidatos() traz o simbolo ao
    pool, o escore o promove
  rejected:
  - chunk cru em literais — ECOA texto da pergunta no pack publicado
    (test_o_texto_da_tarefa_nao_e_ecoado reprova)
  - fatia contigua tolerante a stopword — `[impact]` continuaria menor
    que `[impact, for]`; reordenar stopwords dentro do nome e over-fit
    sem denominador
  rollback: voltar a `nome in literais` apenas
covers:
- part: tree_economy_measurement
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — TREE_ECONOMY_MEASUREMENT

O ponto delicado e o AC4: a primeira tentativa (chunk cru em `literais`)
funcionou para retrieval mas violou o invariante "o pack nao ecoa texto
cru da pergunta". A forma final tem duas asas, ambas no escore — nada
publicado:

1. `run_case` recebe `exact_name` porque `[run, case]` e fatia contigua
   dos literais `[run, case]`.
2. `impact_for` falha a fatia (stopword `for` some da expansao) — a
   igualdade `nome in nomes_identificadores` cobre o caso, com o
   identificador chegando por parametro ao `escore`, e a frase FTS em
   `_candidatos()` garantindo que o simbolo esteja no pool.

Medicao por iteracao: 209/225 → 220/225 → 224/226. Os dois residuais
sao honestos por construcao e ficam nomeados no gate.
