---
sdd: 1
feature: AGENTOPS_AGENT
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENTOPS_AGENT/design.md
  sha256: 4ae2a7482e0f3770a1afd54df1212a4ab92b0fe2fb9fdc0202a9909ff6942e76
tasks:
- id: T1
  files: &id001
  - sparkforge_azure/agentic/spans.py
  - sparkforge_azure/observability/agentops.py
  - tests/test_agentic_spans.py
  covers:
  - AC1
  test:
    path: tests/test_agentic_spans.py
    name: test_agent_span_fields_and_unknown_tokens
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agentic_spans.py
    name: test_execution_receipt_shape
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agentic_spans.py
    name: test_waste_detector
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agentic_spans.py
    name: test_agentops_report_value_vector
---

# Plan — AGENTOPS_AGENT
