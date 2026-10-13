---
sdd: 1
feature: SKILLS_AGENTS_HARDENING
phase: explore
profile: dev
status: done
approaches:
- id: A1
  summary: Reescrever as 22 skills para so citar comandos existentes e marcar o resto
    como planejado
  tradeoffs:
  - nenhum codigo de produto novo
  - skills de PySpark e o judge continuam sem caminho executavel embora os motores
    existam no pacote
- id: A2
  summary: Expor na CLI os verbos cujo motor ja existe (analyze pyspark, judge, knowledge
    select), marcar os demais `analyze <kind>` como planned_tool_refs e fazer o
    validador cruzar tool_refs e comandos do corpo com a CLI real; mirrors de agent
    ganham tools/descricao de acionamento
  tradeoffs:
  - fecha a classe de defeito (ref para comando inexistente passa no validador)
  - muda a superficie da CLI (surface lock regenerado)
chosen: A2 — o eval mostrou que o motor de regras roda via Python; falta so a porta
  de entrada. Ref irresoluvel e defeito de contrato, nao estilo
---

# Explore — SKILLS_AGENTS_HARDENING

Avaliacao das 22 skills e 40 agents (2026-10-09), estatica e empirica (6 casos x
com/sem skill, scratchpad `skills-eval/iteration-1`):

- Todas as skills mandam rodar `sparkforge-azure analyze <kind>`, `judge` e
  `knowledge select`; nenhum existe na CLI (`invalid choice`). Com skill:
  84% das assercoes, 188 s; sem skill: 97%, 109 s. A unica assercao que a skill
  perde e "no maximo 1 tentativa em comando inexistente" — o conteudo nao piora.
- Sintaxe errada em comando que existe: `governance diagnose --scenario
  uc-read-denied --facts` (espera caminho; `--facts` nao existe), `lab run
  skew-join --facts` (cenario e `spark-skew`; `--facts` nao existe).
- `validate_tool_ref` so checa sintaxe contra `CLI_VERBS`; `test_skills` exige
  `sparkforge-azure judge` em todo corpo — o teste fixa o defeito.
- Mirrors `.claude/agents/custom/` sem `tools:` → 40 agents com todas as tools,
  contra `risk: read_only`. `description` = `mission`, 27 com o mesmo sufixo,
  sem "quando usar".
- 15 agents com regra positiva em `does_not` (primeira letra rebaixada:
  "vACUUM so e avaliado..."); dois invertem sentido (`azure-databricks`,
  `adls`).
- "## Quando usar" das skills repete 5 triggers; `analyze-batch-loop` nao esta
  em nenhum agent; termo de rota `scan` captura "full table scan".
