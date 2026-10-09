---
sdd: 1
feature: SKILLS_AGENTS_HARDENING
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/SKILLS_AGENTS_HARDENING/design.md
  sha256: "519922b3860a360f0154cb7bdb387488efa87ad3e89c88205784f381aeb2564c"
tasks:
- id: T1
  files:
  - sparkforge_azure/agentmanifest/mirrors.py
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_skills_agents_hardening.py
    name: test_ac1_mirror_declares_host_tools
- id: T2
  files:
  - sparkforge_azure/agentmanifest/model.py
  - agents/adf-specialist.md
  covers:
  - AC3
  test:
    path: tests/test_skills_agents_hardening.py
    name: test_ac3_does_not_is_negation
- id: T3
  files:
  - sparkforge_azure/cli/cmd_analyze.py
  - sparkforge_azure/cli/main.py
  covers:
  - AC4
  test:
    path: tests/test_cli_analyze_judge.py
    name: test_ac4_analyze_judge_knowledge_roundtrip
- id: T4
  files:
  - sparkforge_azure/skills/model.py
  - skills/azure-databricks/SKILL.md
  covers:
  - AC5
  - AC6
  test:
    path: tests/test_skills_agents_hardening.py
    name: test_ac5_skill_cli_refs_resolve
- id: T5
  files:
  - sparkforge_azure/agentmanifest/routing.py
  - agents/spark-performance-specialist.md
  covers:
  - AC7
  test:
    path: tests/test_skills_agents_hardening.py
    name: test_ac7_batch_loop_wired_and_scan_not_purview
---

# Plan — SKILLS_AGENTS_HARDENING
