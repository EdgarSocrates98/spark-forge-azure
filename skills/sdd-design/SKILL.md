---
name: sdd-design
description: 'Decidir como construir sobre o define selado — SparkForge Azure SDD fase design. Use quando o
  trabalho for design numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - design
  scope:
  - SDD
  - spec-driven development
  - design
  does:
  - conduz a fase design do ciclo SDD com evidencia e gates nomeados
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
  - skills/sdd-design/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---

# sdd-design — fase `design` (SparkForge Azure)

Decidir como construir sobre o define selado.

## Quando usar / nao usar

- Use: trabalho SDD na fase `design` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

1. Desenho sobre Databricks/ADF/Synapse/Fabric conforme o caso.
2. Formato de tabela (Delta/Iceberg) e particionamento.
3. Rollback e caminho de desfazer explicitos.
4. Alternativas descartadas com razao registrada.
5. upstream.sha256 apontando o define selado.

## Artefato

`docs/sdd/<feature>/design.md` com frontmatter `sdd: 1`, `phase: design`,
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

Artefato `design.md` ready → proxima fase `plan.md`.
