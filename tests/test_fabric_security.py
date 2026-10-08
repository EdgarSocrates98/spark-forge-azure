"""SDD ONELAKE_SECURITY_SHORTCUTS — control-plane vs data-plane split."""
from __future__ import annotations

from sparkforge_azure.fabric.pipeline import run_fabric_case

FIXTURES = "tests/fixtures/fabric"


def test_control_plane_ok_data_plane_denied():
    """Viewer has item read (control plane) but no OneLake grant — the deny
    must land on onelake_security, and the conflict must be named."""
    r = run_fabric_case(f"{FIXTURES}/f02_onelake_denied")
    assert r["status"] == "denied"
    assert r["failure_layer"] == "onelake_security"
    stages = {s["layer"]: s["verdict"] for s in r["diagnosis"]["chain"]}
    assert stages["fabric_workspace"] == "allow"
    assert stages["item_permission"] == "allow"
    assert stages["onelake_security"] == "deny"
    assert "item_access_exists_onelake_denies" in r["diagnosis"]["conflicts"]


def test_grant_only_semantics():
    """Grant model: no deny roles exist — a principal without a grant is
    denied by absence, and a role fact must never carry a deny permission."""
    r = run_fabric_case(f"{FIXTURES}/f02_onelake_denied")
    role_facts = [f for f in r["facts"] if f["kind"] == "onelake.security_role"]
    assert role_facts, "fixture must carry OneLake roles"
    for f in role_facts:
        assert f["attrs"]["grant_model"] is True
        assert not any(str(p).lower() == "deny"
                       for p in f["attrs"]["permissions"])


def test_workspace_bypass_roles_skip_onelake():
    """Admin/Member/Contributor already have data-plane access — a Member
    with zero OneLake grants is allowed, not denied."""
    r = run_fabric_case(f"{FIXTURES}/f14_malicious_metadata")
    stages = {s["layer"]: s["verdict"] for s in r["diagnosis"]["chain"]}
    assert stages["onelake_security"] == "allow"


def test_missing_onelake_artifact_is_unresolved_not_allowed():
    r = run_fabric_case(f"{FIXTURES}/f16_viewer_write_denied")
    assert r["failure_layer"] == "item_permission"
    r2 = run_fabric_case(f"{FIXTURES}/f15_insufficient")
    layers = {u["layer"] for u in r2["unresolved"]}
    assert "fabric_workspace" in layers
    assert r2["status"] == "unresolved"
