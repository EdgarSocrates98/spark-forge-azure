---
sdd: 1
feature: AGENT_LABS_SECURITY
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_LABS_SECURITY/design.md
  sha256: b3ea321a35b3a725cf26ca586267adc82631e9b6597116472a5faa695cc369a0
tasks:
- id: T1
  files: &id001
  - evals/agents/
  - tests/fixtures/agentic/
  - tests/test_agentic_labs.py
  - tests/test_agentic_security_lab.py
  covers:
  - AC1
  test:
    path: tests/test_agentic_labs.py
    name: test_routing_lab_expected_specialists
- id: T2
  files: *id001
  covers:
  - AC2
  test:
    path: tests/test_agentic_labs.py
    name: test_negative_routing_lab
- id: T3
  files: *id001
  covers:
  - AC3
  test:
    path: tests/test_agentic_security_lab.py
    name: test_security_lab_denies
- id: T4
  files: *id001
  covers:
  - AC4
  test:
    path: tests/test_agentic_security_lab.py
    name: test_handoff_taint_lab
- id: T5
  files: *id001
  covers:
  - AC5
  test:
    path: tests/test_agentic_labs.py
    name: test_budget_lab_graceful_stop
- id: T6
  files: *id001
  covers:
  - AC6
  test:
    path: tests/test_agentic_security_lab.py
    name: test_memory_poison_rejected
---

# Plan — AGENT_LABS_SECURITY
