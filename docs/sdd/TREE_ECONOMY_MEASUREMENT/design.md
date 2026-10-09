---
sdd: 1
feature: TREE_ECONOMY_MEASUREMENT
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/TREE_ECONOMY_MEASUREMENT/define.md
  sha256: "2933c83830fa7404fc2a165f661384bd12cc506bcf668c22851aea764a5d6b8d"
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
  reason: escore() — exact_name por fatia contigua de tokens do nome;
    _contido_adjacente(); NOTA documentada sobre identificador cru nao
    entrar em literais (echo da pergunta e proibido)
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
  choice: exact_name por _contido_adjacente(tokens_do_nome, literais) —
    sem emitir o identificador cru como literal
  rejected:
  - chunk cru em literais — ECOA texto da pergunta no pack publicado
    (test_o_texto_da_tarefa_nao_e_ecoado reprova)
  - busca de frase no FTS para todo chunk — adiciona query por
    identificador sem provar que o escore compensa; medido depois
  rollback: voltar a `nome in literais` apenas
covers:
- part: tree_economy_measurement
  acceptance: [AC1, AC2, AC3, AC4]
---

# Design — TREE_ECONOMY_MEASUREMENT

O ponto delicado e o AC4: a primeira tentativa (chunk cru em `literais`)
funcionou para retrieval (223/225) mas violou o invariante "o pack nao
eco texto cru da pergunta". A forma final mantem o escore honesto —
`run_case` recebe `exact_name` porque seus tokens `[run, case]` sao fatia
contigua dos literais `[run, case]` da pergunta `run_case` — sem que a
string `run_case` apareca publicada em `expansao.literais`.
