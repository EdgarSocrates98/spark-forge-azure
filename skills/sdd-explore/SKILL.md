---
name: sdd-explore
description: 'Formar uma ideia difusa em decisao de escopo com grill gate — SparkForge Azure SDD fase explore. Use quando o
  trabalho for explore numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - explore
  scope:
  - SDD
  - spec-driven development
  - explore
  does:
  - conduz a fase explore do ciclo SDD com evidencia e gates nomeados
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
  - skills/sdd-explore/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---

# sdd-explore — fase `explore` (SparkForge Azure)

Formar uma ideia difusa em decisao de escopo com grill gate.

## Quando usar / nao usar

- Use: trabalho SDD na fase `explore` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

1. Grill gate: dono da decisao, fora-de-escopo, risco maior, menor versao aceitavel.
2. Descoberta Azure: servicos tocados (Unity Catalog, Delta, Iceberg, OneLake, ADLS, ADF, Synapse, Fabric).
3. Fatos vem de ferramenta; decisao e sempre do humano.
4. Alternativas com trade-offs, riscos e unknowns explicitos.
5. Aprovacao humana registrada antes de abrir o define.

## Artefato

`docs/sdd/<feature>/explore.md` com frontmatter `sdd: 1`, `phase: explore`,
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
- `references/decision-tree.md` — árvore de decisão do grill gate
- `scripts/validate_evidence.py` — validador local do artefato
- `../_shared/references/` — contratos compartilhados
- `../../docs/sdd/templates/` — template da fase

## Handoff

Artefato `explore.md` ready → proxima fase `define.md`.
