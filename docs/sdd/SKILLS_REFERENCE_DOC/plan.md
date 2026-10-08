---
sdd: 1
feature: SKILLS_REFERENCE_DOC
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/SKILLS_REFERENCE_DOC/design.md
  sha256: 2aed54292269a70071c736df57aead3a4d92fbaef39d95af91f34aa73ddc25e1
tasks:
- id: T1
  files:
  - tests/test_skills.py
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_skills.py
    name: test_skills_reference_doc_in_sync
- id: T2
  files:
  - scripts/gen_skills_doc.py
  - docs/reference/skills.md
  - docs/README.md
  - docs/sdd/README.md
  - docs/reference/cli.md
  covers:
  - AC1
  - AC3
  test:
    path: tests/test_skills.py
    name: test_skills_reference_doc_in_sync
---

# Plan — SKILLS_REFERENCE_DOC
