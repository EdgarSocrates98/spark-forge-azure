# Receita — usar as skills do spark-forge-azure

**O quê:** 23 skills canônicas (contrato v1) cobrem os domínios Azure —
storage (ADLS), Bicep, ADF, Databricks, Entra, Event Hubs, FinOps,
networking, observability, Purview, Spark, Synapse, Terraform, Delta,
Fabric (data-engineering, OneLake, Real-Time), Iceberg, Spark perf/streaming
e Unity Catalog — mais as skills de método `analyze-batch-loop` e
`delegate-specialists` (delegação opcional a especialistas irmãos).
**Por que:** a skill carrega o procedimento e os limites ("não faz") —
o agente não precisa reinventar a rota nem ultrapassar a fronteira do domínio.
**Quando:** tarefa num domínio nomeado — "esse job roda igual no Fabric?",
"por que esse cluster custa tanto", "MERGE Delta ficou lento".
**Quando não:** pergunta genérica sem domínio — `agents route` decide, ou
comece pela skill de diagnóstico amplo.

## Passo a passo

```bash
# a skill é um documento canônico em skills/<nome>/SKILL.md — o host a lê
# automaticamente quando instalada (install --host) ou sob demanda:
cat skills/azure-databricks/SKILL.md
```

No host, peça pelo nome — "use a skill `sparkforge-azure-delta-lake` para
revisar este MERGE lento". O trigger textual do frontmatter é o contrato de
"Use quando…" — é o que dispara a skill, não um comando.

## Interpretação

Cada SKILL.md declara `## Faz` / `## Não faz` / `## Pressupõe` /
`## Entrega` — a fronteira é parte do contrato. Skill que "não decide" devolve
evidência e próximo verbo, não uma opinião disfarçada.

## Verificação

`docs/reference/skills.md` é o catálogo gerado das 23 (`gen_skills_doc.py`) —
scope, triggers e evals por kind.

## Limitações

Skills não executam — são procedimento + boundaries. Execução é do host ou
dos verbos (`analyze`, `diagnose`, `migration`, `judge`).

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| skill não disparou | trigger fora do domínio declarado | use o nome exato ou descreva o sintoma que o frontmatter cobre |
| "a skill respondeu fora do escopo" | fronteira mal lida | o `## Não faz` é normativo — devolva ao coordenador |
