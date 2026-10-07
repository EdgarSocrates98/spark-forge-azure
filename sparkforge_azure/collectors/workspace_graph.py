"""``collect workspace-graph`` backend (section 68).

Builds the LIVE workspace graph for a manifest: Resource Graph inventory (from
an offline export by default; from Azure only with ``live=True``), scoped to
the subscriptions the manifest declares.  Out-of-scope observations are
dropped and counted -- the manifest is the authorization boundary.  Declared
resources are matched to observations by ARM id only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sparkforge_azure.collectors import resource_graph
from sparkforge_azure.collectors.base import CollectorInputError, CollectorResult
from sparkforge_azure.collectors.redact import assert_clean
from sparkforge_azure.graph.arm import parse_arm_id
from sparkforge_azure.graph.live import live_graph_from_facts
from sparkforge_azure.graph.model import azure_node_id
from sparkforge_azure.graph.workspace import WorkspaceManifest, load_workspace_manifest


def collect_workspace_graph(
    manifest: WorkspaceManifest | str | Path,
    *,
    export: str | Path | None = None,
    live: bool = False,
    collector: resource_graph.ResourceGraphCollector | None = None,
    hash_principals: bool = False,
) -> dict[str, Any]:
    wm = manifest if isinstance(manifest, WorkspaceManifest) else load_workspace_manifest(
        manifest)
    scope = set(wm.subscriptions())
    if live:
        if not scope:
            raise CollectorInputError("manifest declares no ARM-scoped resource (no subscription)")
        rg = collector or resource_graph.ResourceGraphCollector(sorted(scope))
        result: CollectorResult = rg.collect(hash_principals=hash_principals)
    else:
        if export is None:
            raise CollectorInputError("offline mode needs --export (cloud read requires --live)")
        result = resource_graph.from_export(export, hash_principals=hash_principals)
    in_scope = []
    out_of_scope = 0
    for fact in result.facts:
        sub = parse_arm_id(fact.subject["arm_id"]).subscription_id.lower()
        if scope and sub not in scope:
            out_of_scope += 1
            continue
        in_scope.append(fact)
    graph = live_graph_from_facts(in_scope, source=resource_graph.SOURCE)
    declared = {r.name: azure_node_id(r.arm_id) for r in wm.cloud_resources if r.arm_id}
    matched = sorted(name for name, nid in declared.items() if nid in graph.nodes)
    missing = sorted(set(declared) - set(matched))
    for name in missing:
        graph.add_unresolved({"reason": "declared_not_observed", "resource": name,
                              "id": declared[name]})
    graph.meta = {"kind": "live", "workspace": wm.name, "mode": result.mode,
                  "observed_at": result.observed_at}
    out = {
        "status": "ok",
        "workspace": wm.name,
        "mode": result.mode,
        "observed_at": result.observed_at,
        "scope_subscriptions": sorted(scope),
        "records": result.records,
        "facts": len(in_scope),
        "out_of_scope": out_of_scope,
        "declared_matched": matched,
        "declared_missing": missing,
        "redaction": result.redaction.to_dict(),
        "graph": graph.to_dict(),
    }
    assert_clean(out)
    return out


__all__ = ["collect_workspace_graph"]
