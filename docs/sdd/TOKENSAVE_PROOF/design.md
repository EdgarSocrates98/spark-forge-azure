---
sdd: 1
feature: TOKENSAVE_PROOF
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/TOKENSAVE_PROOF/define.md
  sha256: "a03b533d31558499f1611ff501185a3a1162dc2a96b3b77e844daee6e9e64f83"
files:
  - {path: sparkforge_azure/tokensave/benchmark.py, action: create, reason: "compara baseline vs profiles no caso real; métricas medidas do ledger"}
  - {path: sparkforge_azure/cli/cmd_tokensave.py, action: modify, reason: "tokensave benchmark --case"}
  - {path: tests/test_tokensave_benchmark.py, action: create, reason: "prova as 4 ACs"}
  - {path: evals/token_efficient/access_case/, action: create, reason: "corpus do caso UC/ADLS para o benchmark"}
  - {path: docs/tokensave/benchmark.md, action: create, reason: "registro reproduzível das medidas"}
decisions:
  - id: D1
    choice: "baseline = soma dos bytes do corpus do caso (leitura integral), medido no mesmo artefato"
    rejected: ["baseline sintético: não é o caso real"]
    rollback: "n/d"
  - id: D2
    choice: "tokens fora do ledger = 'unresolved' explícito, nunca estimativa"
    rejected: ["constantes de custo: viola 'SEM NUMERO INVENTADO'"]
    rollback: "n/d"
covers:
  - {part: benchmark, acceptance: [AC1, AC2]}
  - {part: ladder, acceptance: [AC3, AC4]}
---

# Design — TOKENSAVE_PROOF

`benchmark.py` monta o caso (lista de artefatos do bundle + termos exigidos),
roda `TokenSave.context()` em cada profile e compara com o custo de ler o
corpus inteiro. O resultado é dict serializável com `tokens: unresolved` quando
não há provider — medida honesta, não marketing.
