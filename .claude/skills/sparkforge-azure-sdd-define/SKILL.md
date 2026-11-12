---
name: sparkforge-azure-sdd-define
description: 'Fixar o que significa pronto: hipotese + criterios AC* verificaveis — SparkForge Azure SDD fase define. Use quando o
  trabalho for define numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - define
  scope:
  - SDD
  - spec-driven development
  - define
  does:
  - conduz a fase define do ciclo SDD com evidencia e gates nomeados
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
  - skills/sdd-define/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---
<!-- GENERATED from skills/sdd-define/SKILL.md; do not edit -->
# sdd-define — fase `define` (SparkForge Azure)

Fixar o que significa pronto: hipotese + criterios AC* verificaveis.

## Quando usar / nao usar

- Use: trabalho SDD na fase `define` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

1. Hipotese mensuravel e metrica de sucesso.
2. Criterios AC1..ACn verificaveis por comando.
3. Requisitos de dados Azure: business keys, deduplicacao, consistencia, idempotencia, reprocessamento, SLA.
4. Seguranca: Entra ID, RBAC, Unity Catalog grants afetados.
5. status ready somente com ACs completos.

## Artefato

`docs/sdd/<feature>/define.md` com frontmatter `sdd: 1`, `phase: define`,
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

Artefato `define.md` ready → proxima fase `design.md`.
