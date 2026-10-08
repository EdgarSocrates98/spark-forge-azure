"""Pipeline offline end-to-end: bundle -> facts -> diagnose -> failure_layer -> receipt."""
from __future__ import annotations

import json
from pathlib import Path

from sparkforge_azure.azure import pipeline

FIXTURES = Path(__file__).parent / "fixtures" / "access"


def test_pipeline_end_to_end_offline(tmp_path: Path) -> None:
    bundle = tmp_path / "case"
    bundle.mkdir()
    (bundle / "case.yaml").write_text(
        "name: e2e\n"
        "principal: {id: spn-job-1, type: service_principal}\n"
        "operation: read\n"
        "target:\n"
        "  kind: path\n"
        "  url: abfss://lake@stg.dfs.core.windows.net/finance/orders\n"
        "compute:\n"
        "  workspace_id: '1234567890123456'\n"
        "  type: classic_vnet\n",
        encoding="utf-8",
    )
    (bundle / "unity_catalog.json").write_text(json.dumps({
        "storage_credentials": {"cred1": {"identity_id": "mi-1",
                                          "access_connector_id": "/ac/ac1"}},
        "external_locations": [{"name": "loc1", "credential": "cred1",
                                "url": "abfss://lake@stg.dfs.core.windows.net/finance"}],
        "grants": [{"securable": "external_location:loc1", "principal": "spn-job-1",
                    "privileges": ["READ FILES"]}],
    }), encoding="utf-8")
    (bundle / "rbac.json").write_text(json.dumps({"assignments": [
        {"principal": "mi-1", "role": "Storage Blob Data Contributor",
         "scope": "/subscriptions/s1/resourceGroups/rg/providers/"
                  "Microsoft.Storage/storageAccounts/stg/blobServices/default/"
                  "containers/lake"},
    ]}), encoding="utf-8")
    (bundle / "adls.json").write_text(json.dumps({
        "account_id": "/subscriptions/s1/resourceGroups/rg/providers/"
                      "Microsoft.Storage/storageAccounts/stg",
        "hns": True}), encoding="utf-8")
    (bundle / "network.json").write_text(json.dumps({"default_action": "Allow"}),
                                        encoding="utf-8")
    (bundle / "entra.json").write_text(json.dumps(
        {"principals": {"spn-job-1": {"enabled": True},
                        "mi-1": {"enabled": True}}}), encoding="utf-8")
    (bundle / "notebooks").mkdir()
    (bundle / "notebooks" / "job.py").write_text(
        'spark.read.load("abfss://lake@stg.dfs.core.windows.net/finance/orders")\n',
        encoding="utf-8")

    report = pipeline.run_case(bundle)

    assert report["status"] == "pass"
    assert report["case"] == "e2e"
    assert report["failure_layer"] is None
    assert report["diagnosis"]["status"] == "allowed"
    # facts extraídos dos artefatos e do notebook
    kinds = {f["kind"] for f in report["facts"]}
    assert "unity_catalog.external_location" in kinds
    assert "azure_rbac.assignment" in kinds
    assert "notebook.abfss_path" in kinds
    # recibo com campos obrigatórios
    receipt = report["receipt"]
    for key in ("case", "profile", "tools", "sources", "facts", "rules",
                "findings", "agents", "budget", "unresolved"):
        assert key in receipt, key
    assert receipt["case"] == "e2e"
    assert receipt["budget"]["cloud_access"] is False
    # evidence path: findings citam fatos ancorados em arquivos do bundle
    assert "evidence_paths" in report
    for finding, paths in report["evidence_paths"].items():
        assert paths, finding
    # grafo de acesso: principal -> target + layers avaliadas com proveniência
    g = report["access_graph"]
    node_ids = {n["id"] for n in g["nodes"]}
    assert "azure:identity:spn-job-1" in node_ids
    assert any(n["kind"] == "filesystem" for n in g["nodes"])
    rels = {e["relation"] for e in g["edges"]}
    assert "accesses" in rels
    assert "verdict_allow" in rels
    assert all(n["provenance"]["kind"] == "artifact" for n in g["nodes"])


def test_evidence_path_from_graph() -> None:
    """AC4: every finding carries a graph-derived evidence path.

    finding node -> evidenced_by -> fact nodes -> provenance source artifact.
    """
    report = pipeline.run_case(FIXTURES / "s01_uc_privilege_denied")
    assert report["status"] == "denied"
    g = report["access_graph"]
    nodes = {n["id"]: n for n in g["nodes"]}
    assert any(n["kind"] == "finding" for n in nodes.values())
    findings_paths = {
        rule: p for rule, p in report["evidence_paths"].items()
        if "graph_path" in p
    }
    assert findings_paths, "no graph-derived evidence path emitted"
    for rule, paths in findings_paths.items():
        gp = paths["graph_path"]
        assert gp["facts"], f"{rule}: no fact nodes"
        assert gp["artifacts"], f"{rule}: no source artifacts"
        finding_nid = f"evidence:finding:{rule}"
        evidenced = {
            (e["source"], e["target"]) for e in g["edges"]
            if e["relation"] == "evidenced_by" and e["source"] == finding_nid
        }
        assert evidenced, f"{rule}: no evidenced_by edge in graph"
        for _src, fact_nid in evidenced:
            fact_node = nodes.get(fact_nid)
            assert fact_node is not None, f"{fact_nid} not a node"
            assert fact_node["provenance"]["kind"] == "artifact"
            assert fact_node["provenance"]["source"]
        # the path ends at the bundle artifact files
        assert gp["path"][0] == finding_nid
        assert set(gp["artifacts"]).issubset(set(gp["path"]))
