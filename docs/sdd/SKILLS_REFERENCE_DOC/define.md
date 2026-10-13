---
sdd: 1
feature: SKILLS_REFERENCE_DOC
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/SKILLS_REFERENCE_DOC/explore.md
  sha256: ddf83b45f3912ff964c1296e21704d81e2f194382dc5f6af5d6c4340fad03a9e
hypothesis:
  claim: Um catalogo de skills gerado deterministicamente do SKILL.md evita drift
    documental; grill gate documentado fortalece o intake SDD
  prediction: docs/reference/skills.md reflete 22 skills (triggers, handoffs, eval
    kinds); teste de sync reprova doc stale
  experiment: pytest tests/test_skills.py -k skills_doc
acceptance:
- id: AC1
  statement: docs/reference/skills.md e gerado por scripts/gen_skills_doc.py e cobre
    as 22 skills
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_skills_reference_doc_in_sync
- id: AC2
  statement: doc stale (editada a mao) produz falha nomeada no teste de sync
  verified_by:
    kind: test
    ref: tests/test_skills.py::test_skills_reference_doc_in_sync
- id: AC3
  statement: docs/sdd/README.md documenta o grill gate mapeado nos campos SDD
  verified_by:
    kind: test
    ref: tests/test_sdd_cli.py::test_sdd_readme_documents_grill_gate
success:
- id: SC1
  metric: catalogo em sync; index de docs cobre o novo arquivo
  source: pytest tests/test_skills.py && scripts/check_docs_index.py
out_of_scope:
- mudar o contrato v1 das skills
- verbos novos de CLI
unknowns: []
change_kinds:
- agent_or_skill
- knowledge_doc
---

# Define — SKILLS_REFERENCE_DOC
