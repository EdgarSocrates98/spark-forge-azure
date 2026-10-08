"""SDD FABRIC_CORE — collectors/fabric.py: export mode + opt-in live mode."""
from __future__ import annotations

import pytest

from sparkforge_azure.collectors import fabric as fc
from sparkforge_azure.collectors.base import CollectorInputError, CollectorUnavailable

FIXTURES = "tests/fixtures/fabric"


def test_from_export_items():
    r = fc.from_export(f"{FIXTURES}/f14_malicious_metadata/items.json",
                       artifact="items")
    kinds = {f.kind for f in r.facts}
    assert "fabric.lakehouse" in kinds
    assert r.mode == "export"
    assert r.redaction is not None and r.redaction.count >= 0


def test_from_export_unknown_artifact():
    with pytest.raises(CollectorInputError):
        fc.from_export(f"{FIXTURES}/f14_malicious_metadata/items.json",
                       artifact="wat")


def test_live_requires_injected_fetch():
    with pytest.raises(CollectorUnavailable):
        fc.collect_live(workspace_id="ws-1111")


def test_live_inventory_with_fetch_double():
    """Injected fetch double returns list payloads; failures -> unresolved."""
    calls = []

    def fetch(method, url):
        calls.append(url)
        if "items" in url:
            return {"value": [{"id": "lh-1", "type": "Lakehouse",
                               "workspaceId": "ws-1111",
                               "displayName": "lh"}]}
        raise TimeoutError("lakehouses endpoint down")

    r = fc.collect_live(workspace_id="ws-1111", fetch=fetch,
                        observed_at="2026-10-08T00:00:00Z")
    assert r.mode == "live"
    assert r.observed_at == "2026-10-08T00:00:00Z"
    assert any(u["what"] == "lakehouses" for u in r.unresolved)
    assert {u["failure_class"] for u in r.unresolved} == {"network"}
    # only GET read-only endpoints were issued
    assert all("api.fabric.microsoft.com/v1/workspaces/ws-1111" in u
               for u in calls)


def test_fingerprint_axes():
    from sparkforge_azure.fabric.fingerprint import fabric_fingerprint
    from sparkforge_azure.findings.models import Fact
    facts = [Fact(kind="environment.scope",
                  subject={"source": "s", "key": "tenant_id",
                           "value": "t-1"},
                  attrs={"key": "tenant_id", "value": "t-1"})]
    fp = fabric_fingerprint({"target": {"workspace_id": "ws-9"}}, facts)
    assert fp["axes"]["tenant_id"] == "t-1"
    assert fp["axes"]["workspace_id"] == "ws-9"
    assert "capacity_id" not in fp["axes"]  # absent, never invented
