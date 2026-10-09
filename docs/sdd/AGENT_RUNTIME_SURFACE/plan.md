---
sdd: 1
feature: AGENT_RUNTIME_SURFACE
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/AGENT_RUNTIME_SURFACE/design.md
  sha256: a796252211e561b40b9aacce0e69ae03ecb5166800f30df12bce8ebdaddbfe76
tasks:
- id: T1
  files: [tests/test_runtime_surface.py]
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_runtime_surface.py
    name: test_mcp_tools_readonly
- id: T2
  files:
  - sparkforge_azure/agentic/spans.py
  - sparkforge_azure/cli/cmd_agents.py
  - sparkforge_azure/mcp/agent_tools.py
  - sparkforge_azure/doctor.py
  covers: [AC1, AC2, AC3, AC4]
  test:
    path: tests/test_runtime_surface.py
    name: test_spans_carry_runtime_fields
---

# Plan — AGENT_RUNTIME_SURFACE
