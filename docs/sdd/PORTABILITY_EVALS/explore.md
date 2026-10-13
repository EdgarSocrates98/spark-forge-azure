---
sdd: 1
feature: PORTABILITY_EVALS
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: "Runner de matriz em `evals/portability/` (suite.yaml declara
      casos + expect; runner.py executa em temp dirs com HOME/XDG falsos) +
      `scripts/check_portability.py` como gate §188 com modo --wheel (T3)"
    tradeoffs:
      - segue a convenção evals/convergence; gate separado dos testes
        unitários; wheel prova wheel-only de verdade
  - id: B
    summary: Tudo como pytest em tests/
    tradeoffs:
      - "o spec separa prova de portabilidade (evals/) de unit tests; e o
        wheel gate precisa de subprocess/venv — mais gate que teste"
  - id: C
    summary: Só o gate estático, sem wheel real
    tradeoffs:
      - "§194 declara o installed-wheel gate obrigatório para fechar a wave"
chosen: A
---

# PORTABILITY_EVALS — explore

O spec (§92–§101, §187–§204) pede a prova da portabilidade: matriz de casos
(single/monorepo/multi/relocated/copied/direct/transitive/host-unavailable/
mcp-only/detach-reattach), isolamento de HOME, gate anti-drift e a prova
T3 com wheel instalado fora do checkout. O runner dirige a API
`distribution` em temp dirs; o gate checa assets/schema/docs/mirrors/
checkout-dependency e, com `--wheel`, builda e instala em venv temporário
e corre o ciclo inteiro a partir do pacote instalado.

## Evidência prévia

- `evals/convergence/runner.py` — convenção suite.yaml + runner + reports.
- `tests/` W1–W6 — unidade por caso já verde; aqui a prova é o ciclo
  integrado por cenário.
