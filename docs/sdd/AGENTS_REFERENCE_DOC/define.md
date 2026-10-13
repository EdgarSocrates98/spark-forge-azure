---
sdd: 1
feature: AGENTS_REFERENCE_DOC
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/AGENTS_REFERENCE_DOC/explore.md
  sha256: 05c80e43ee13b8144ed1825162fbb0243aaec20eae34bf04fc51426ad5699474
hypothesis:
  claim: docs/reference/agents.md gerado deterministicamente de agents/*.md cobre
    os 40 agents
  prediction: sync test reprova edicao manual; doc indexada em docs/README.md
  experiment: pytest tests/test_agents_doc.py
acceptance:
- id: AC1
  statement: agents.md lista os 40 agents com kind, domain, autonomy, evals e mirrors
  verified_by:
    kind: test
    ref: tests/test_agents_doc.py::test_agents_doc_in_sync
- id: AC2
  statement: regen e idempotente; doc indexada em docs/README.md
  verified_by:
    kind: test
    ref: tests/test_agents_doc.py::test_agents_doc_indexed
success:
- id: SC1
  metric: agents.md em sync com o corpus
  source: pytest tests/test_agents_doc.py
out_of_scope:
- doc autoral adicional
unknowns: []
change_kinds:
- knowledge_doc
- tool_or_verb
---

# Define — AGENTS_REFERENCE_DOC
