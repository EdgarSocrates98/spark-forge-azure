---
sdd: 1
feature: SKILL_HANDOFF_RESOLUTION
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_HANDOFF_RESOLUTION/design.md
  sha256: a4a78ab4c635a1883f3c3b7292774aee588df47cf5814ea96f49934196cf7f55
tasks:
- id: T1
  files:
  - tests/test_skills.py
  covers:
  - AC1
  - AC3
  test:
    path: tests/test_skills.py
    name: test_handoff_targets_resolve
- id: T2
  files:
  - skills/azure-synapse/SKILL.md
  - skills/iceberg/SKILL.md
    - skills/analyze-batch-loop/SKILL.md
  covers:
  - AC2
  test:
    path: tests/test_skills.py
    name: test_handoff_targets_resolve
- id: T3
  files:
  - sparkforge_azure/skills/model.py
  covers:
  - AC1
  - AC3
  test:
    path: tests/test_skills.py
    name: test_handoff_target_unknown_refused
---

# Plan — SKILL_HANDOFF_RESOLUTION
