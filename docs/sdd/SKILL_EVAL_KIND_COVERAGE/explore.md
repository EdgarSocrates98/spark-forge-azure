---
sdd: 1
feature: SKILL_EVAL_KIND_COVERAGE
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Estender VERTICAL_SKILLS para todas as 22 no contrato
  tradeoffs:
  - enforcement nativo
  - muda semantica do contrato v1 por distincao deliberada
- id: A2
  summary: Teste na arvore real exige negative+boundary em todas; evals novos respeitam
    grounding
  tradeoffs:
  - mesmo enforcement no repo
  - contrato intacto
chosen: A2 — a exigencia vertical e deliberada; o que falta e cobertura real, nao
  contrato
---

# Explore — SKILL_EVAL_KIND_COVERAGE

As 8 skills nao-verticais so tem casos positive (kind default). Verticais
exigem negative+boundary por decisao de contrato — mas o par bicep/terraform,
purview/unity-catalog e spark/databricks tem dominio adjacente e precisa de
trigger negativo para nao sobre-disparar.
