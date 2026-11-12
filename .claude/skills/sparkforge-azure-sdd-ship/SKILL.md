---
name: sparkforge-azure-sdd-ship
description: 'Fechar o ciclo com evidencia de entrega e hypothesis_outcome — SparkForge Azure SDD fase ship. Use quando o
  trabalho for ship numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - ship
  scope:
  - SDD
  - spec-driven development
  - ship
  does:
  - conduz a fase ship do ciclo SDD com evidencia e gates nomeados
  - selo upstream.sha256 via `sparkforge-azure sdd stamp` apos mudanca intencional
  does_not:
  - nao executa comandos nem assume servicos de outro provedor de nuvem
  - nao aprova fase sem artefato selado e gate verde
  - nao decide escopo nem hipotese sem aprovacao humana
  knowledge_refs:
  - knowledge/azure/databricks/
  tool_refs:
  - sparkforge-azure sdd check
  - sparkforge-azure sdd stamp
  eval_refs:
  - skills/sdd-ship/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---
<!-- GENERATED from skills/sdd-ship/SKILL.md; do not edit -->
# sdd-ship — fase `ship` (SparkForge Azure)

Fechar o ciclo com evidencia de entrega e hypothesis_outcome.

## Quando usar / nao usar

- Use: trabalho SDD na fase `ship` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

1. `sparkforge-azure sdd check --feature F` limpo antes de marcar ready.
2. Registros do change_kind citados (ver docs/gates-por-mudanca.md).
3. hypothesis_outcome: confirmada ou refutada, com evidencia.
4. Rollback testado ou declarado nao-reversivel.
5. upstream.sha256 apontando o build_report selado.

## Artefato

`docs/sdd/<feature>/ship.md` com frontmatter `sdd: 1`, `phase: ship`,
`status` e `upstream.sha256` da fase anterior — re-sele com
`sparkforge-azure sdd stamp <path>` apos mudanca intencional.

## Pontos de decisão

- Gate: `sparkforge-azure sdd check --feature <f>` — cada recusa e nomeada e carrega `unlock`; existencia de arquivo nunca e prova.
- `upstream_hash_stale` → re-stamp apos mudanca intencional.
- `schema_invalid` → corrigir frontmatter, nunca contornar.
- `evidence_missing` → produzir o artefato/AC, nunca override.

## Não concluir sem evidência

- Artefato selado + `sparkforge-azure sdd check` verde sao o minimo; status pronto sem os dois e defeito.

## Seguranca

- Sem credenciais em artefatos; identidades Entra/RBAC citadas por nome, nao por segredo.
- Mudanca em producao passa por aprovacao humana — a skill nao aprova.

## Handoff

Ship aceito → ciclo fechado; aprendizado volta ao define da proxima feature.
