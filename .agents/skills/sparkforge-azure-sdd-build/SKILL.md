---
name: sparkforge-azure-sdd-build
description: 'Executar o plano com evidencia: red/green, recibo, recuperacao idempotente — SparkForge Azure SDD fase build_report. Use quando o
  trabalho for build_report numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - build_report
  scope:
  - SDD
  - spec-driven development
  - build_report
  does:
  - conduz a fase build_report do ciclo SDD com evidencia e gates nomeados
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
  - skills/sdd-build/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---
<!-- GENERATED from skills/sdd-build/SKILL.md; do not edit -->
# sdd-build — fase `build_report` (SparkForge Azure)

Executar o plano com evidencia: red/green, recibo, recuperacao idempotente.

## Quando usar / nao usar

- Use: trabalho SDD na fase `build_report` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

1. Executar tasks em ordem; cada uma produz prova citavel.
2. red -> green registrado por task no build_report.
3. Perfil operator: mudanca so via fluxo governado de sandbox.
4. Recovery checkpoint: re-run retoma sem duplicar efeito.
5. upstream.sha256 apontando o plan selado.

## Artefato

`docs/sdd/<feature>/build_report.md` com frontmatter `sdd: 1`, `phase: build_report`,
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

Artefato `build_report.md` ready → proxima fase `ship.md`.
