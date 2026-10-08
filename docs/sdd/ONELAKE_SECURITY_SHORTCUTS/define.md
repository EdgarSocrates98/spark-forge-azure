---
sdd: 1
feature: ONELAKE_SECURITY_SHORTCUTS
phase: define
profile: dev
status: done
upstream:
  path: docs/sdd/ONELAKE_SECURITY_SHORTCUTS/explore.md
  sha256: "d713e0bcfe7dbe012a8540edc0a686ef6c0b3df63e60fbcca1a38673834ef6a3"
hypothesis:
  claim: Modelar control-plane vs data-plane como facts separados permite dizer 'workspace permission OK, OneLake data permission DENIED' e distinguir passthrough (caller identity) de delegated (connection
    identity) na cadeia shortcut→target
  prediction: fixtures com workspace-role ok + onelake role ausente produzem failure_layer=onelake_security; shortcut delegated com connection sem acesso produz shortcut_auth/source_access com effective_identity
    explícita
  experiment: pytest tests/test_fabric_security.py tests/test_fabric_shortcuts.py
acceptance:
- id: AC1
  statement: control plane (workspace roles Admin/Member/Contributor/Viewer + item permissions) e data plane (OneLake security roles grant-only, Read/ReadWrite, scopes folder/table/schema/row/column) são
    facts e findings separados
  verified_by:
    kind: test
    ref: tests/test_fabric_security.py::test_control_plane_ok_data_plane_denied
- id: AC2
  statement: 'OneLake grant-only model respeitado: sem evidence de deny semantics não se afirma blocked/filtered; RLS/CLS só em Read roles; Admin/Member/Contributor bypass data-plane (doc-sourced)'
  verified_by:
    kind: test
    ref: tests/test_fabric_security.py::test_grant_only_semantics
- id: AC3
  statement: 'shortcut passthrough: effective_identity=caller; delegated: effective_identity=connection/workspace-identity; nunca colapsar; DirectLake-SQL delegated exception registrada em knowledge'
  verified_by:
    kind: test
    ref: tests/test_fabric_shortcuts.py::test_passthrough_vs_delegated_identity
- id: AC4
  statement: effective identity ≠ caller identity exposta no report; confused-deputy (caller sem source perm, delegated com acesso) não conclui 'caller tem acesso'
  verified_by:
    kind: test
    ref: tests/test_fabric_shortcuts.py::test_confused_deputy_not_collapsed
- id: AC5
  statement: failure layers shortcut/shortcut_auth/source_access só com evidence; target metadata ausente → unresolved
  verified_by:
    kind: test
    ref: tests/test_fabric_shortcuts.py::test_missing_target_metadata_unresolved
success:
- id: SC1
  metric: security chain workspace→item→onelake→shortcut→auth→target verde em fixtures com evidence path grafo-backed
  source: pytest tests/test_fabric_security.py tests/test_fabric_shortcuts.py
out_of_scope:
- live OneLake API
- Warehouses/PowerBI security deep
unknowns: []
change_kinds:
- extractor
- rule
- fixture_corpus
---

# Define — ONELAKE_SECURITY_SHORTCUTS

Artefatos do Cycle 3 (Fabric deep vertical); ver prompt_evo_cycle3.md.
