---
name: sdd-plan
description: 'Quebrar a construcao em tarefas com teste e criterio executaveis sem contexto — SparkForge Azure SDD fase plan. Use quando o
  trabalho for plan numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - plan
  scope:
  - SDD
  - spec-driven development
  - plan
  does:
  - conduz a fase plan do ciclo SDD com evidencia e gates nomeados
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
  - skills/sdd-plan/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---

# sdd-plan — fase `plan` (SparkForge Azure)

Quebrar a construcao em tarefas com teste e criterio executaveis sem contexto.

## Quando usar / nao usar

- Use: trabalho SDD na fase `plan` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

1. Tasks T1..Tn pequenas, cada uma com teste red -> green.
2. Cada task cobre ao menos um AC do define.
3. Prova esperada por task e um comando, nao prosa.
4. Arquivos por task limitados aos declarados no design.
5. upstream.sha256 apontando o design selado.

## Artefato

`docs/sdd/<feature>/plan.md` com frontmatter `sdd: 1`, `phase: plan`,
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

## Referências

- `references/README.md` — guia da fase
- `references/task-graph.md` — DAG de tarefas e cobertura de critérios
- `scripts/validate_evidence.py` — validador local do artefato
- `../_shared/references/` — contratos compartilhados
- `../../docs/sdd/templates/` — template da fase

## Handoff

Artefato `plan.md` ready → proxima fase `build_report.md`.
