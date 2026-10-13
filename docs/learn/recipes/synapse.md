# Receita — Azure Synapse

**O quê:** Synapse é coberto por `migration inventory|assess` (Synapse →
Fabric, o caminho documentado) e pela skill `azure-synapse` (Spark pools,
pipelines Synapse, SQL pools, autopause/autoscale, versão fora de suporte).
**Por que:** "migrar Synapse para Fabric ou Databricks?" é a pergunta real —
o assessment compara readiness por artefato e o plano sai com waves e
rollback, nunca com suposição.
**Quando:** pipeline Synapse falhando, Spark pool fora de suporte,
decisão de migração, autopause mal configurado.
**Quando não:** Fabric (`diagnose fabric`), ADF (`migration` + skill
`azure-data-factory`) — Synapse, Fabric e ADF são produtos diferentes.

## Passo a passo

```bash
sparkforge-azure migration inventory --bundle <dir-do-estate>
sparkforge-azure migration assess --bundle <dir-do-estate>
sparkforge-azure migration plan --bundle <dir-do-estate>     # waves + rollback
sparkforge-azure migration validate --bundle <dir-do-estate> # pós-migração
```

Quatro verbos, quatro momentos: `inventory` (censo) → `assess` (prontidão +
recomendações) → `plan` (ondas, blockers, rollback) → `validate` (dimensões
de validação pós-migração).

## Interpretação

Readiness por artefato + blockers nomeados. `plan` nunca propõe ordem sem
declarar dependência upstream — blocker é dado, não opinião.

## Verificação

`tests/fixtures/migration` tem 22 cenários cobrindo Synapse e ADF —
`migration assess --suite` confere cada `expect:`.

## Limitações

O export é a fronteira: artefato fora do ARM export não existe para o
assessment. SQL pool dedicado vs. serverless têm readiness diferentes —
o relatório separa.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| "Fabric e Synapse são a mesma coisa" | confusão de produto | são pipelines e modelos diferentes — a skill `azure-synapse` documenta o boundary |
| wave ignora ordem | dependência entre pipelines | `plan` já ordena por upstream; veja `upstream_blockers` |
