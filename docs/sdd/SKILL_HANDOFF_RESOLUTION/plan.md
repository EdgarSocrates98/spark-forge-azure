---
sdd: 1
feature: SKILL_HANDOFF_RESOLUTION
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/SKILL_HANDOFF_RESOLUTION/design.md
  sha256: 1bb645e12a5cbbc2071201e5ed09893a5e9ee1b388bd2d13233d30f375e84a49
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
    - tests/test_architecture_layers.py
  covers:
  - AC1
  - AC3
  test:
    path: tests/test_skills.py
    name: test_handoff_target_unknown_refused
---

# Plan — SKILL_HANDOFF_RESOLUTION
