---
sdd: 1
feature: ONELAKE_SECURITY_SHORTCUTS
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/ONELAKE_SECURITY_SHORTCUTS/design.md
  sha256: "a78ab9e56ef72ecf3cb025a7ef809d7224e74487d23582a41fc83dc5cfd14306"
tasks:
- id: T1
  files:
  - sparkforge_azure/fabric/security.py
  covers:
  - AC1
  - AC2
  test:
    path: tests/test_fabric_security.py
    name: test_control_plane_ok_data_plane_denied
- id: T2
  files:
  - sparkforge_azure/fabric/shortcuts.py
  covers:
  - AC3
  - AC4
  - AC5
  test:
    path: tests/test_fabric_shortcuts.py
    name: test_passthrough_vs_delegated_identity
---

# Plan — ONELAKE_SECURITY_SHORTCUTS

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
