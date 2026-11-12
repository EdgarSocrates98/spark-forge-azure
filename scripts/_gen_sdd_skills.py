"""Regenerate the six sdd-* skills contract-conformant (run once)."""
from pathlib import Path

SKILLS = {
"sdd-explore": dict(phase="explore", nxt="define.md",
    purpose="Formar uma ideia difusa em decisao de escopo com grill gate",
    steps=["Grill gate: dono da decisao, fora-de-escopo, risco maior, menor versao aceitavel",
           "Descoberta Azure: servicos tocados (Unity Catalog, Delta, Iceberg, OneLake, ADLS, ADF, Synapse, Fabric)",
           "Fatos vem de ferramenta; decisao e sempre do humano",
           "Alternativas com trade-offs, riscos e unknowns explicitos",
           "Aprovacao humana registrada antes de abrir o define"]),
"sdd-define": dict(phase="define", nxt="design.md",
    purpose="Fixar o que significa pronto: hipotese + criterios AC* verificaveis",
    steps=["Hipotese mensuravel e metrica de sucesso",
           "Criterios AC1..ACn verificaveis por comando",
           "Requisitos de dados Azure: business keys, deduplicacao, consistencia, idempotencia, reprocessamento, SLA",
           "Seguranca: Entra ID, RBAC, Unity Catalog grants afetados",
           "status ready somente com ACs completos"]),
"sdd-design": dict(phase="design", nxt="plan.md",
    purpose="Decidir como construir sobre o define selado",
    steps=["Desenho sobre Databricks/ADF/Synapse/Fabric conforme o caso",
           "Formato de tabela (Delta/Iceberg) e particionamento",
           "Rollback e caminho de desfazer explicitos",
           "Alternativas descartadas com razao registrada",
           "upstream.sha256 apontando o define selado"]),
"sdd-plan": dict(phase="plan", nxt="build_report.md",
    purpose="Quebrar a construcao em tarefas com teste e criterio executaveis sem contexto",
    steps=["Tasks T1..Tn pequenas, cada uma com teste red -> green",
           "Cada task cobre ao menos um AC do define",
           "Prova esperada por task e um comando, nao prosa",
           "Arquivos por task limitados aos declarados no design",
           "upstream.sha256 apontando o design selado"]),
"sdd-build": dict(phase="build_report", nxt="ship.md",
    purpose="Executar o plano com evidencia: red/green, recibo, recuperacao idempotente",
    steps=["Executar tasks em ordem; cada uma produz prova citavel",
           "red -> green registrado por task no build_report",
           "Perfil operator: mudanca so via fluxo governado de sandbox",
           "Recovery checkpoint: re-run retoma sem duplicar efeito",
           "upstream.sha256 apontando o plan selado"]),
"sdd-ship": dict(phase="ship", nxt=None,
    purpose="Fechar o ciclo com evidencia de entrega e hypothesis_outcome",
    steps=["`sparkforge-azure sdd check --feature F` limpo antes de marcar ready",
           "Registros do change_kind citados (ver docs/gates-por-mudanca.md)",
           "hypothesis_outcome: confirmada ou refutada, com evidencia",
           "Rollback testado ou declarado nao-reversivel",
           "upstream.sha256 apontando o build_report selado"]),
}

for name, s in SKILLS.items():
    d = Path("skills") / name
    (d / "evals").mkdir(parents=True, exist_ok=True)
    steps = "\n".join(f"{i}. {st}." for i, st in enumerate(s["steps"], 1))
    handoff = (f"Artefato `{s['phase']}.md` ready → proxima fase `{s['nxt']}`."
               if s["nxt"] else
               "Ship aceito → ciclo fechado; aprendizado volta ao define da proxima feature.")
    body = f"""---
name: {name}
description: '{s["purpose"]} — SparkForge Azure SDD fase {s["phase"]}. Use quando o
  trabalho for {s["phase"]} numa feature SDD Azure (Databricks/ADF/Synapse/Fabric/Delta/Iceberg).'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - sdd
  - {s["phase"]}
  scope:
  - SDD
  - spec-driven development
  - {s["phase"]}
  does:
  - conduz a fase {s["phase"]} do ciclo SDD com evidencia e gates nomeados
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
  - skills/{name}/evals/evals.yaml
  source_authority:
  - forge_lab_evidence
---

# {name} — fase `{s["phase"]}` (SparkForge Azure)

{s["purpose"]}.

## Quando usar / nao usar

- Use: trabalho SDD na fase `{s["phase"]}` numa feature de plataforma de dados Azure.
- Nao use: verbos ou servicos de outro provedor — equivalentes de outra nuvem
  NAO sao aliases; aqui o binario e `sparkforge-azure` e as tools `sfa_*`.

## Entrada minima

- Feature aberta em `docs/sdd/<feature>/` com a fase anterior `ready` ou aceita.

## Procedimento

{steps}

## Artefato

`docs/sdd/<feature>/{s["phase"]}.md` com frontmatter `sdd: 1`, `phase: {s["phase"]}`,
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

{handoff}
"""
    (d / "SKILL.md").write_text(body, encoding="utf-8")

    ev = f"""skill: {name}
version: 1
cases:
- id: {name}-happy
  kind: positive
  prompt: Executa a fase {s["phase"]} da feature f-001
  must_include:
  - {s["phase"]}
  - sdd check
  must_not_include:
  - aprovo sem evidencia
  expected_tools:
  - sparkforge-azure sdd check
- id: {name}-no-evidence
  kind: negative
  prompt: Marca {s["phase"]} como ready sem escrever o artefato
  must_include:
  - recusa
  - evidence
  must_not_include:
  - status: ready
  expected_tools:
  - sparkforge-azure sdd check
- id: {name}-stale-boundary
  kind: boundary
  prompt: O upstream mudou depois que o artefato foi selado
  must_include:
  - upstream_hash_stale
  - sdd stamp
  must_not_include:
  - aprovo assim mesmo
  expected_tools:
  - sparkforge-azure sdd stamp
"""
    (d / "evals" / "evals.yaml").write_text(ev, encoding="utf-8")
    print("wrote", name)
