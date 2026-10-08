---
sdd: 1
feature: ONELAKE_SECURITY_SHORTCUTS
phase: plan
profile: dev
status: done
upstream:
  path: docs/sdd/ONELAKE_SECURITY_SHORTCUTS/design.md
  sha256: "22ca2ae5bd8f115c6bb6e0d33b9d999579c34baa4a931bccac90171a20ec8d6e"
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
