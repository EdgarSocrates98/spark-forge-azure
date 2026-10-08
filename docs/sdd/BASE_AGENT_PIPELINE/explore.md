---
sdd: 1
feature: BASE_AGENT_PIPELINE
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: usar ExecutionGraph generico como a pipeline
  tradeoffs:
  - grafo e runtime de evidencias, nao a cadeia §30
- id: A2
  summary: BASE_AGENT_PIPELINE declarativa (nos required|conditional) + plan_pipeline
    deterministico que poda condicionais
  tradeoffs:
  - minimo e honesto
  - nao executa — so planeja a cadeia
chosen: A2 — §30/31 pedem a cadeia canonica declarada com branches condicionais
---

# Explore — BASE_AGENT_PIPELINE

§30 define a cadeia canonica; §31/32 definem poda condicional (evidence completa + baixo risco -> pula specialist/reviewer). graph.py e grafo de evidencias, nao a cadeia de execucao.
