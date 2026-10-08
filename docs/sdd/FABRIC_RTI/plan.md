---
sdd: 1
feature: FABRIC_RTI
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/FABRIC_RTI/design.md
  sha256: "7fe45c0f05b257c589aad3574a740d7180ae9f3fc64135398ace7f349e3df486"
tasks:
- id: T1
  files:
  - sparkforge_azure/stream/rti.py
  - rules/catalog/rti.yaml
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_stream_rti.py
    name: test_eventstream_facts
---

# Plan — FABRIC_RTI

Artefatos do Cycle 4; ver prompt_evo_cycle4.md.
