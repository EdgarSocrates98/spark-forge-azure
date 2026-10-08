"""SDD FABRIC_CORE — extractors produce Facts; SaaS topology, never ARM."""
from __future__ import annotations

from sparkforge_azure.fabric import extract
from sparkforge_azure.fabric.casefile import load_bundle

FIXTURES = "tests/fixtures/fabric"


def test_fabric_artifacts_become_facts():
    bundle = load_bundle(f"{FIXTURES}/f14_malicious_metadata")
    facts = extract.extract_all(bundle.artifacts, bundle.sources)
    kinds = {f.kind for f in facts}
    for expected in ("fabric.workspace", "fabric.capacity", "fabric.lakehouse",
                     "onelake.table", "environment.scope"):
        assert expected in kinds, expected
    for f in facts:
        assert f.provenance.get("mode") == "bundle"
        assert f.provenance.get("source")


def test_saas_topology_not_arm():
    """Fabric ids are GUID-ish workspace/item ids — the extractors must never
    fabricate an ARM ``/subscriptions/...`` id for them."""
    bundle = load_bundle(f"{FIXTURES}/f14_malicious_metadata")
    facts = extract.extract_all(bundle.artifacts, bundle.sources)
    for f in facts:
        for value in f.subject.values():
            assert not str(value).startswith("/subscriptions/"), (f.kind, f.subject)
        for key, value in f.attrs.items():
            if isinstance(value, str):
                assert "/subscriptions/" not in value or key == "target_url"


def test_display_name_never_identity():
    """Two items with the same display_name must stay distinct by id."""
    facts = extract.extract_items(
        {"items": [
            {"id": "a-1", "type": "Notebook", "workspace_id": "w",
             "display_name": "dup"},
            {"id": "a-2", "type": "Notebook", "workspace_id": "w",
             "display_name": "dup"}]},
        {"source": "t", "mode": "bundle"})
    subjects = {str(f.subject["item_id"]) for f in facts
                if f.kind == "fabric.notebook"}
    assert subjects == {"a-1", "a-2"}


def test_secret_keys_redacted_at_boundary():
    facts = extract.extract_all(
        {"connections": {"c1": {"type": "adls_gen2",
                                "client_secret": "super-secret-value",
                                "connection_string": "AccountKey=abc"}}},
        {"connections": "connections.json"})
    blob = " ".join(str(f.attrs) for f in facts)
    assert "super-secret-value" not in blob
    assert "AccountKey=abc" not in blob
