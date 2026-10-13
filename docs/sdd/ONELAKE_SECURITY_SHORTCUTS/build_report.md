---
sdd: 1
feature: ONELAKE_SECURITY_SHORTCUTS
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/ONELAKE_SECURITY_SHORTCUTS/plan.md
  sha256: "911fb34cb5dede3576aa443e930654c0a5d4024da03226b7335292f1c781a98d"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_security.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_security.py -q", exit: 0}
  - id: T2
    status: done
    red: {command: "cd .tmp-base-red && python -m pytest tests/test_fabric_shortcuts.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_fabric_shortcuts.py -q", exit: 0}
claims:
  - text: "control plane ok + data plane negado diagnostica camada de dados, nao workspace"
    evidence_ref: "tests/test_fabric_security.py::test_control_plane_ok_data_plane_denied"
  - text: "OneLake security roles sao grant-only: ausencia de grant nunca vira deny inventado"
    evidence_ref: "tests/test_fabric_security.py::test_grant_only_semantics"
  - text: "passthrough avalia identidade do caller; delegated avalia connection/workspace identity — nunca misturados"
    evidence_ref: "tests/test_fabric_shortcuts.py::test_passthrough_vs_delegated_identity"
  - text: "caller e effective identity preservados separadamente (confused deputy nao colapsado)"
    evidence_ref: "tests/test_fabric_shortcuts.py::test_confused_deputy_not_collapsed"
  - text: "shortcut sem metadata de target e unresolved, nao missing-permission"
    evidence_ref: "tests/test_fabric_shortcuts.py::test_missing_target_metadata_unresolved"
---

# Build Report — ONELAKE_SECURITY_SHORTCUTS

Red em worktree base `068b922` (pre-Fabric), green em `feat/cycle3-fabric-deep`. Detalhes no frontmatter.
