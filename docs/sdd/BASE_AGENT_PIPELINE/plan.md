---
sdd: 1
feature: BASE_AGENT_PIPELINE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/BASE_AGENT_PIPELINE/design.md
  sha256: 8d3616716fc5df46cbfa8afb7532d1d33d887c2e0494ee1286fdb7f6d8a5d490
tasks:
- id: T1
  files:
  - tests/test_agentic_pipeline.py
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_agentic_pipeline.py
    name: test_base_pipeline_order
- id: T2
  files:
  - sparkforge_azure/agentic/pipeline.py
  covers:
  - AC1
  - AC2
  - AC3
  - AC4
  test:
    path: tests/test_agentic_pipeline.py
    name: test_fast_path_skips_optionals
---

# Plan — BASE_AGENT_PIPELINE
