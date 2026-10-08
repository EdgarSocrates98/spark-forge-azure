---
sdd: 1
feature: TOKENSAVE_PROOF
phase: explore
profile: dev
status: done
approaches:
  - id: A1
    summary: "Benchmark honesto `tokensave/benchmark.py`: mesmo caso (falha de acesso UC/ADLS) sob baseline (leitura ingênua) vs economy/balanced/deep; métricas medidas do ledger (bytes lidos/evitados, distribuição por nível, taxas de full-read/index/cache/reuse); tokens só quando provider observado"
    tradeoffs:
      - baseline = custo de ler o corpus inteiro do caso; byte-economy é medida real, token-economy fica `unresolved`
  - id: A2
    summary: Estimar economia por constantes fixas
    tradeoffs:
      - proibido pela cultura do repo ("SEM NUMERO INVENTADO") e pelo prompt
  - id: A3
    summary: Benchmark só em teste, sem doc nem eval
    tradeoffs:
      - a prova precisa ser reproduzível e registrada
chosen: A1
---

# Explore — TOKENSAVE_PROOF

## Estado atual (audit)

- `tokensave/engine.py`: ladder L0-L6 (`context()` para no primeiro nível suficiente), `read_full` exige profile deep + reason, `ledger` por sessão.
- `tokensave/levels.py`: profiles economy/balanced/deep com budgets e limites de expansão.
- `tokensave/ledger.py`: `RetrievalRecord` por chamada (nível, bytes, cache hit, reuse, fallback, outcome), `summary()` agrega.
- `evals/token_efficient/` existe com fixtures de qualidade/decisão.

## O que falta

Benchmark reproduzível do caso real do vertical com métricas honestas (bytes sim, tokens só se observados), prova de "para no primeiro nível suficiente", taxa de leitura integral rara, e integração do resultado no recibo do diagnóstico.
