"""Resource Graph collector: offline export -> redaction -> facts -> graph nodes.

All fixture data is SYNTHETIC (fixtures/azure/).
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

from sparkforge_azure.collectors import cost, databricks, monitor, resource_graph
from sparkforge_azure.collectors.auth import describe_auth
from sparkforge_azure.collectors.base import CollectorInputError, CollectorUnavailable
from sparkforge_azure.collectors.workspace_graph import collect_workspace_graph

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "azure"
ARG = FIX / "arg_export.json"
# No secret literal lives in fixtures or in this source: tests inject freshly
# generated fake values into a temporary copy of the synthetic export.
ACCOUNT_KEY = "Account" + "Key"
SHARED_KEY = "SharedAccess" + "Key"
CLIENT_SECRET = "client" + "Secret"
BEARER = "Bear" + "er"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _secrets() -> dict[str, str]:
    jwt = ".".join([
        _b64url(json.dumps({"alg": "none"}).encode()),
        _b64url(json.dumps({"sub": secrets.token_hex(8)}).encode()),
        _b64url(os.urandom(24)),
    ])
    return {"storage": base64.b64encode(os.urandom(64)).decode(),
            "sas": secrets.token_hex(16), "sb": secrets.token_hex(16), "jwt": jwt,
            "client": secrets.token_urlsafe(24)}


@pytest.fixture()
def seeded(tmp_path):
    """ARG export copy with generated secrets in properties -> (path, values)."""

    gen = _secrets()
    data = json.loads(ARG.read_text(encoding="utf-8"))
    by_name = {r["name"] + r["subscriptionId"][-4:]: r for r in data["data"]}
    lake = by_name["stlakehouseaaaa"]["properties"]
    lake["diagnosticConnection"] = (f"DefaultEndpointsProtocol=https;AccountName=stlakehouse;"
                                    f"{ACCOUNT_KEY}={gen['storage']};EndpointSuffix=x")
    lake["exportUrl"] = ("https://stlakehouse.blob.core.windows.net/e/x.csv?sv=2022-11-02&"
                         f"sig={gen['sas']}")
    by_name["evhns-ingestaaaa"]["properties"]["note"] = (
        f"Endpoint=sb://evhns-ingest.servicebus.windows.net/;SharedAccessKeyName=Root;"
        f"{SHARED_KEY}={gen['sb']}")
    kv = by_name["kv-platformaaaa"]["properties"]
    kv["lastAuditHeader"] = f"Authorization: {BEARER} {gen['jwt']}"
    kv[CLIENT_SECRET] = gen["client"]
    path = tmp_path / "arg_seeded.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, list(gen.values())


def test_from_export_produces_facts_with_arm_subject():
    res = resource_graph.from_export(ARG)
    assert res.mode == "export" and res.records == 9 and len(res.facts) == 9
    assert res.observed_at == "2026-10-01T12:00:00+00:00"
    kinds = {f.kind for f in res.facts}
    assert kinds == {"azure.resource"}
    subjects = sorted(f.subject["arm_id"] for f in res.facts)
    assert all(s.startswith("/subscriptions/") and s == s.lower() for s in subjects)
    assert len(set(subjects)) == 9
    assert all(f.provenance["source"] == "azure.resource_graph" for f in res.facts)
    again = resource_graph.from_export(ARG)
    assert [f.id for f in again.facts] == [f.id for f in res.facts]


def test_fixture_has_no_secret_material():
    raw = ARG.read_text(encoding="utf-8")
    for marker in ("sig=", ACCOUNT_KEY + "=", SHARED_KEY + "=", "eyJ", BEARER + " "):
        assert marker not in raw


def test_injected_secrets_are_redacted_everywhere(seeded):
    path, values = seeded
    raw = path.read_text(encoding="utf-8")
    assert all(v in raw for v in values)  # the export really carries the fake secrets
    res = resource_graph.from_export(path)
    out = json.dumps(res.to_dict()) + resource_graph.to_graph(res).to_json()
    for value in values:
        assert value not in out
    assert res.redaction.count >= 5
    assert "connection_secret" in res.redaction.kinds


def test_graph_nodes_kinds_and_hierarchy():
    g = resource_graph.to_graph(resource_graph.from_export(ARG))
    by_name = {n.attrs.get("name"): n for n in g.nodes.values() if n.attrs.get("fact_id")}
    assert by_name["dbw-analytics"].kind == "databricks_workspace"
    assert by_name["ac-dbw-analytics"].kind == "identity"
    assert by_name["evhns-ingest"].kind == "event_hub"
    assert by_name["fabcapprod"].kind == "fabric_capacity"
    assert by_name["pe-stlakehouse-dfs"].kind == "network"
    assert by_name["kv-platform"].kind == "key_vault"
    assert by_name["dbw-analytics"].attrs["databricks_workspace_id"] == "1234567890123456"
    assert all(n.provenance.kind == "live" for n in g.nodes.values())
    assert all(n.provenance.observed_at for n in g.nodes.values())
    dbw = by_name["dbw-analytics"].id
    assert (dbw, "references", by_name["ac-dbw-analytics"].id) in g.edges
    assert any(k[0] == dbw and k[1] == "located_in" for k in g.edges)
    stshared = [n for n in g.nodes.values() if n.attrs.get("name") == "stshared"]
    assert len(stshared) == 2


def test_no_sdk_imported_at_import_time():
    code = (
        "import sys\n"
        "import sparkforge_azure.collectors as c\n"
        "import sparkforge_azure.collectors.resource_graph, sparkforge_azure.collectors.auth\n"
        "import sparkforge_azure.collectors.databricks, sparkforge_azure.collectors.cost\n"
        "import sparkforge_azure.collectors.monitor, sparkforge_azure.collectors.workspace_graph\n"
        "import sparkforge_azure.graph\n"
        "bad = sorted(m for m in sys.modules if m == 'azure' or m.startswith(('azure.', "
        "'databricks.', 'msal')) or m == 'databricks')\n"
        "print(bad)\n"
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=str(ROOT), env=env, check=True, timeout=120)
    assert out.stdout.strip() == "[]"


class _Page:
    def __init__(self, data, skip_token):
        self.data = data
        self.skip_token = skip_token


class _FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.requests = []

    def resources(self, request):
        self.requests.append(request)
        return self.pages[len(self.requests) - 1]


def test_live_collect_paginates_with_skip_token_using_injected_client(seeded):
    path, values = seeded
    records = json.loads(path.read_text(encoding="utf-8"))["data"]
    client = _FakeClient([_Page(records[:4], "tok1"), _Page(records[4:8], "tok2"),
                          _Page(records[8:], None)])
    collector = resource_graph.ResourceGraphCollector(
        ["00000000-0000-4000-8000-00000000AAAA"], client=client,
        request_builder=lambda subs, q, skip, top: {"subs": subs, "skip": skip, "top": top,
                                                    "query": q},
    )
    res = collector.collect(observed_at="2026-10-02T00:00:00+00:00")
    assert [r["skip"] for r in client.requests] == [None, "tok1", "tok2"]
    assert client.requests[0]["subs"] == ("00000000-0000-4000-8000-00000000aaaa",)
    assert client.requests[0]["query"] == resource_graph.ARG_QUERY
    assert res.mode == "live" and len(res.facts) == 9
    assert all(f.provenance["mode"] == "live" for f in res.facts)
    assert not any(v in json.dumps(res.to_dict()) for v in values)


def test_live_without_sdk_raises_collector_unavailable():
    if importlib.util.find_spec("azure") is not None and importlib.util.find_spec(
            "azure.mgmt.resourcegraph") is not None:
        pytest.skip("azure extra installed")
    with pytest.raises(CollectorUnavailable, match="sparkforge-azure\\[azure\\]"):
        resource_graph.ResourceGraphCollector(["00000000-0000-4000-8000-00000000aaaa"]).collect()


def test_auth_description_is_offline_and_never_echoes_secrets(monkeypatch):
    value = secrets.token_urlsafe(24)
    monkeypatch.setenv("AZURE_CLIENT_SECRET", value)
    d = describe_auth("service_principal")
    assert d["env_present"]["AZURE_CLIENT_SECRET"] is True
    assert value not in json.dumps(d)
    with pytest.raises(ValueError):
        describe_auth("password")


def test_bad_exports_are_refused(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(CollectorInputError):
        resource_graph.from_export(bad)
    bad.write_text('{"data": "nope"}', encoding="utf-8")
    with pytest.raises(CollectorInputError):
        resource_graph.from_export(bad)
    bad.write_text('[{"id": "not-an-arm-id", "name": "x"}]', encoding="utf-8")
    res = resource_graph.from_export(bad)
    assert res.facts == [] and res.unresolved == [{"reason": "invalid_arm_id", "record": 0}]


def test_raw_persistence_is_redacted_and_gitignored(tmp_path, seeded):
    path, values = seeded
    raw_dir = tmp_path / ".sparkforge-azure" / "raw"
    res = resource_graph.from_export(path, raw_dir=raw_dir)
    written = Path(res.raw_path).read_text(encoding="utf-8")
    assert not any(v in written for v in values)
    assert (raw_dir / ".gitignore").read_text(encoding="utf-8").strip() == "*"


def test_workspace_graph_scoped_to_declared_subscriptions():
    out = collect_workspace_graph(ROOT / "examples" / "workspace", export=ARG)
    assert out["status"] == "ok" and out["mode"] == "export"
    assert out["records"] == 9 and out["facts"] == 8 and out["out_of_scope"] == 1
    assert out["declared_matched"] == ["analytics", "lake", "shared-storage"]
    ids = {n["id"] for n in out["graph"]["nodes"]}
    assert not any("00000000bbbb" in i for i in ids)
    with pytest.raises(CollectorInputError):
        collect_workspace_graph(ROOT / "examples" / "workspace")


def test_databricks_cost_monitor_exports(tmp_path):
    token_value, key_value, sig_value = (secrets.token_hex(12) for _ in range(3))
    dbx_data = json.loads((FIX / "databricks_export.json").read_text(encoding="utf-8"))
    dbx_data["jobs"][1]["settings"]["spark_env_vars"] = {"STORAGE_" + "TOKEN": token_value}
    dbx_data["clusters"][0]["spark_conf"] = {
        "fs.azure.account." + "key" + ".stlakehouse.dfs.core.windows.net": key_value}
    dbx_path = tmp_path / "dbx.json"
    dbx_path.write_text(json.dumps(dbx_data), encoding="utf-8")
    dbx = databricks.from_export(dbx_path)
    kinds = sorted({f.kind for f in dbx.facts})
    assert kinds == ["databricks.cluster", "databricks.job", "unity_catalog.catalog"]
    dumped = json.dumps(dbx.to_dict())
    assert token_value not in dumped and key_value not in dumped
    c = cost.from_export(FIX / "cost_export.csv")
    costs = {f.subject["resource_id"].rsplit("/", 1)[-1]: f.measures["cost"] for f in c.facts}
    assert costs == {"dbw-analytics": 123.45, "stlakehouse": None}  # unknown is not zero
    logs = json.loads((FIX / "log_analytics_export.json").read_text(encoding="utf-8"))
    logs["tables"][0]["rows"][0][2] += f"?sv=2022-11-02&sig={sig_value}"
    log_path = tmp_path / "logs.json"
    log_path.write_text(json.dumps(logs), encoding="utf-8")
    m = monitor.from_export(log_path)
    assert len(m.facts) == 2
    assert sig_value not in json.dumps(m.to_dict())


@pytest.mark.live_azure
def test_live_resource_graph_smoke():
    if os.environ.get("SPARKFORGE_AZURE_LIVE") != "1":
        pytest.skip("live Azure tests need SPARKFORGE_AZURE_LIVE=1")
    sub = os.environ.get("SPARKFORGE_AZURE_SUBSCRIPTION_ID")
    if not sub:
        pytest.skip("SPARKFORGE_AZURE_SUBSCRIPTION_ID not set")
    res = resource_graph.ResourceGraphCollector([sub]).collect()
    assert res.mode == "live"
    json.dumps(res.to_dict())  # to_dict runs assert_clean
