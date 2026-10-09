---
sdd: 1
feature: AGENTS_REFERENCE_DOC
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENTS_REFERENCE_DOC/design.md
  sha256: 22ca53c24a66ca55d4e32274e7ee636555680fdd8769fc1ad974940f790573c0
tasks:
- id: T1
  files:
  - tests/test_agents_doc.py
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_agents_doc.py
    name: test_agents_doc_in_sync
- id: T2
  files:
  - scripts/gen_agents_doc.py
  - docs/reference/agents.md
  - docs/README.md
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_agents_doc.py
    name: test_agents_doc_indexed
---

# Plan — AGENTS_REFERENCE_DOC
