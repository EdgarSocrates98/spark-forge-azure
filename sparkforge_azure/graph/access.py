"""Access-chain graph builder (P0-C): access facts -> typed nodes/edges.

Reads the deterministic Facts of the access vertical (``unity_catalog.*``,
``azure_rbac.assignment``, ``adls.*``, ``databricks.*``, ``notebook.*``) and
emits the governed-access chain::

    job --uses--> cluster
    job --executes--> notebook
    notebook --reads|writes--> table
    notebook --accesses--> filesystem
    external_location --uses--> storage_credential
    storage_credential --uses_identity--> access_connector (ARM node)
    access_connector --exposes_identity--> managed identity
    identity --has_role--> role_assignment --applies_to--> scope (ARM)
    external_location --points_to--> filesystem
    filesystem --located_in--> storage_account (ARM node)
    table --located_at--> external_location
    catalog --bound_to--> databricks workspace
    principal --has_privilege--> securable --governs--> table
    principal --accesses--> target   (when a case is given)

Two passes: nodes first, edges second -- a fact early in deterministic order
may reference a node produced by a later fact (external_location < credential
alphabetically).  Every edge is derived from an explicit id/url carried as a
fact attribute -- never from display-name coincidence.  A referenced object
absent from the facts produces no edge and lands in ``graph.unresolved``.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.abfss import split_abfss
from sparkforge_azure.graph.arm import is_arm_id, kind_for_arm_id, parse_arm_id
from sparkforge_azure.graph.model import (
    Edge,
    Graph,
    Node,
    Provenance,
    node_id,
)
from sparkforge_azure.graph.model import (
    azure_node_id as _arm_node,
)

# Relations the access queries traverse.  Kept here (single vocabulary) so
# query code and tests share the same list.
ACCESS_RELATIONS = frozenset({
    "accesses", "applies_to", "bound_to", "executes", "exposes_identity",
    "governs", "has_privilege", "has_role", "located_at", "part_of",
    "points_to", "reads", "uses", "uses_identity", "writes",
})

_WRITE_OPS = frozenset({"MERGE", "INSERT", "UPDATE", "DELETE", "OPTIMIZE",
                        "VACUUM", "RESTORE"})

_UC = "azure:unity_catalog:"


def _prov(fact: Mapping[str, Any]) -> Provenance:
    """Fact provenance -> graph provenance.  Live observations stay live."""
    raw = fact.get("provenance") or {}
    src = str(raw.get("source") or "unknown")
    kind = "live" if str(raw.get("mode")) == "live" else "artifact"
    return Provenance(kind, src, raw.get("observed_at"))


def _add(graph: Graph, nid: str, kind: str, layer: str, prov: Provenance,
         attrs: Mapping[str, Any] | None = None) -> str:
    graph.add_node(Node(nid, kind, layer, dict(attrs or {}), prov))
    return nid


def _fs_id(url: str) -> str | None:
    """abfss url -> filesystem node id ``azure:filesystem:acct/container/path``."""
    parts = split_abfss(url)
    if parts is None:
        return None
    account, container, path = parts
    return node_id("azure", "filesystem", f"{account}/{container}{path}".rstrip("/"))


def _cred_id(name: str) -> str:
    return _UC + f"storage_credential:{name}"


def _loc_id(name: str) -> str:
    return _UC + f"external_location:{name}"


def _catalog_id(name: str) -> str:
    return _UC + f"catalog:{name}"


def _securable_id(name: str) -> str:
    return _UC + f"securable:{name}"


def _ws_id(workspace_id: str) -> str:
    return f"azure:databricks:{workspace_id}"


# ---------------------------------------------------------------- nodes pass

def _nodes_uc(graph: Graph, fact: Mapping[str, Any]) -> None:
    prov = _prov(fact)
    kind = fact["kind"]
    subject = fact.get("subject") or {}
    attrs = fact.get("attrs") or {}
    if kind == "unity_catalog.storage_credential":
        name = subject.get("name")
        if not name:
            graph.add_unresolved({"reason": "missing_subject", "fact": fact.get("id")})
            return
        _add(graph, _cred_id(str(name)), "unity_catalog", "azure", prov,
             {"name": name, "uc_object": "storage_credential",
              "fact_id": fact.get("id")})
        conn = str(attrs.get("access_connector_id") or "")
        if is_arm_id(conn):
            extra = attrs.get("_connector_attrs")
            _add(graph, _arm_node(conn), "identity", "azure", prov,
                 {"via": "storage_credential", "fact_id": fact.get("id"),
                  **(dict(extra) if isinstance(extra, Mapping) else {})})
        elif conn:
            graph.add_unresolved({"reason": "credential_connector_not_arm_id",
                                  "storage_credential": name})
        mid = str(attrs.get("identity_id") or "")
        if mid:
            _add(graph, node_id("azure", "identity", mid), "identity", "azure",
                 prov, {"managed_identity_id": mid, "fact_id": fact.get("id")})
    elif kind == "unity_catalog.external_location":
        name = subject.get("name")
        if not name:
            graph.add_unresolved({"reason": "missing_subject", "fact": fact.get("id")})
            return
        _add(graph, _loc_id(str(name)), "unity_catalog", "azure", prov,
             {"name": name, "uc_object": "external_location",
              "url": attrs.get("url"), "fact_id": fact.get("id")})
    elif kind == "unity_catalog.catalog":
        name = subject.get("name")
        if name:
            _add(graph, _catalog_id(str(name)), "unity_catalog", "azure", prov,
                 {"name": name, "uc_object": "catalog",
                  "isolation_mode": attrs.get("isolation_mode"),
                  "fact_id": fact.get("id")})
    elif kind == "unity_catalog.table":
        name = subject.get("name")
        if not name:
            graph.add_unresolved({"reason": "missing_subject", "fact": fact.get("id")})
            return
        _add(graph, node_id("data", "table", str(name)), "table", "data", prov,
             {"name": name, "format": attrs.get("format"),
              "location": attrs.get("location"), "fact_id": fact.get("id")})
    elif kind == "unity_catalog.grant":
        principal, securable = subject.get("principal"), subject.get("securable")
        if not principal or not securable:
            graph.add_unresolved({"reason": "grant_incomplete",
                                  "fact": fact.get("id")})
            return
        _add(graph, node_id("azure", "identity", str(principal)), "identity",
             "azure", prov, {"principal_id": principal})
        _add(graph, _securable_id(str(securable)), "unity_catalog", "azure",
             prov, {"name": securable, "uc_object": "securable"})


def _nodes_rbac(graph: Graph, fact: Mapping[str, Any]) -> None:
    prov = _prov(fact)
    subject = fact.get("subject") or {}
    attrs = fact.get("attrs") or {}
    principal = str(subject.get("principal") or "")
    scope = str(subject.get("scope") or "")
    if not principal or not scope:
        graph.add_unresolved({"reason": "assignment_incomplete",
                              "fact": fact.get("id")})
        return
    _add(graph, node_id("azure", "identity", principal), "identity", "azure",
         prov, {"principal_id": principal})
    _add(graph, node_id("azure", "resource",
                        f"roleAssignment:{principal}@{scope.lower()}"),
         "resource", "azure", prov,
         {"role": attrs.get("role"), "principal": principal,
          "scope": scope.lower(), "fact_id": fact.get("id")})
    if is_arm_id(scope):
        _add(graph, _arm_node(scope), kind_for_arm_id(scope), "azure", prov,
             {"arm_id": scope.lower()})


def _nodes_adls(graph: Graph, fact: Mapping[str, Any]) -> None:
    if fact["kind"] != "adls.account":
        return
    prov = _prov(fact)
    account_id = str((fact.get("subject") or {}).get("account_id") or "")
    if is_arm_id(account_id):
        _add(graph, _arm_node(account_id), "storage_account", "azure", prov,
             {"arm_id": account_id.lower(),
              "hns": (fact.get("attrs") or {}).get("hns"),
              "fact_id": fact.get("id")})


def _nodes_compute(graph: Graph, fact: Mapping[str, Any]) -> None:
    if fact["kind"] != "databricks.compute":
        return
    prov = _prov(fact)
    attrs = fact.get("attrs") or {}
    ws = str(attrs.get("workspace_id") or "")
    if ws:
        _add(graph, _ws_id(ws), "databricks_workspace", "azure", prov,
             {"databricks_workspace_id": ws})
    cluster_id = str(attrs.get("cluster_id") or "")
    if cluster_id and ws:
        _add(graph, node_id("data", "cluster", f"databricks:{ws}/{cluster_id}"),
             "cluster", "data", prov,
             {"cluster_id": cluster_id, "workspace_id": ws,
              "data_security_mode": attrs.get("data_security_mode"),
              "fact_id": fact.get("id")})
    job_id = str(attrs.get("job_id") or "")
    if job_id and ws:
        _add(graph, node_id("data", "job", f"databricks:{ws}/{job_id}"), "job",
             "data", prov, {"job_id": job_id, "workspace_id": ws,
                            "fact_id": fact.get("id")})
    notebook_path = str(attrs.get("notebook_path") or "")
    if notebook_path:
        _add(graph, node_id("data", "notebook", notebook_path), "notebook",
             "data", prov, {"path": notebook_path, "fact_id": fact.get("id")})


def _nodes_notebook(graph: Graph, fact: Mapping[str, Any]) -> None:
    kind, subject = fact["kind"], fact.get("subject") or {}
    attrs = fact.get("attrs") or {}
    file = subject.get("file")
    if not file or kind == "notebook.analyzed":
        return
    prov = _prov(fact)
    _add(graph, node_id("data", "notebook", str(file)), "notebook", "data", prov,
         {"path": file})
    if kind == "notebook.abfss_path":
        fs = _fs_id(str(attrs.get("url") or ""))
        if fs:
            _add(graph, fs, "filesystem", "azure", prov,
                 {"url": attrs.get("url")})
    elif kind in ("notebook.uc_table", "notebook.write_table", "notebook.delta_op",
                  "notebook.sql_op"):
        table = str(attrs.get("table") or attrs.get("target") or "")
        if table.count(".") == 2:
            _add(graph, node_id("data", "table", table), "table", "data", prov,
                 {"name": table})


# ---------------------------------------------------------------- edges pass

def _edges_uc(graph: Graph, fact: Mapping[str, Any]) -> None:
    prov = _prov(fact)
    kind = fact["kind"]
    subject = fact.get("subject") or {}
    attrs = fact.get("attrs") or {}
    if kind == "unity_catalog.storage_credential":
        name = subject.get("name")
        conn = str(attrs.get("access_connector_id") or "")
        if name and is_arm_id(conn):
            graph.add_edge(Edge(_cred_id(str(name)), "uses_identity",
                                _arm_node(conn), {}, prov))
            mid = str(attrs.get("identity_id") or "")
            if mid:
                graph.add_edge(Edge(_arm_node(conn), "exposes_identity",
                                    node_id("azure", "identity", mid), {}, prov))
    elif kind == "unity_catalog.external_location":
        name = subject.get("name")
        if not name:
            return
        loc = _loc_id(str(name))
        cred_name = str(attrs.get("credential") or "")
        if cred_name:
            cred = _cred_id(cred_name)
            if cred in graph.nodes:
                graph.add_edge(Edge(loc, "uses", cred, {}, prov))
            else:
                graph.add_unresolved({"reason": "credential_not_observed",
                                      "external_location": name,
                                      "credential": cred_name})
        fs = _fs_id(str(attrs.get("url") or ""))
        if fs:
            _add(graph, fs, "filesystem", "azure", prov,
                 {"url": attrs.get("url")})
            graph.add_edge(Edge(loc, "points_to", fs, {}, prov))
        elif attrs.get("url"):
            graph.add_unresolved({"reason": "location_url_not_abfss",
                                  "external_location": name})
    elif kind == "unity_catalog.binding":
        catalog = subject.get("catalog")
        workspaces = attrs.get("workspaces") or []
        if not catalog:
            return
        cat = _catalog_id(str(catalog))
        if not workspaces:
            graph.add_unresolved({"reason": "isolated_catalog_no_workspaces",
                                  "catalog": catalog})
        for ws in sorted(str(w) for w in workspaces):
            _add(graph, _ws_id(ws), "databricks_workspace", "azure", prov,
                 {"databricks_workspace_id": ws})
            graph.add_edge(Edge(cat, "bound_to", _ws_id(ws), {}, prov))
    elif kind == "unity_catalog.table":
        name = subject.get("name")
        if not name:
            return
        loc_url = str(attrs.get("location") or "").rstrip("/")
        if not loc_url:
            return
        for nid in sorted(graph.nodes):
            node = graph.nodes[nid]
            if (node.kind != "unity_catalog"
                    or node.attrs.get("uc_object") != "external_location"):
                continue
            url = str(node.attrs.get("url") or "").rstrip("/")
            if loc_url == url or loc_url.startswith(url + "/"):
                graph.add_edge(Edge(node_id("data", "table", str(name)),
                                    "located_at", nid, {}, prov))
    elif kind == "unity_catalog.grant":
        principal, securable = subject.get("principal"), subject.get("securable")
        if not principal or not securable:
            return
        graph.add_edge(Edge(node_id("azure", "identity", str(principal)),
                            "has_privilege", _securable_id(str(securable)),
                            {"privileges": list(attrs.get("privileges") or [])},
                            prov))
        # The 3-part securable name IS the table's UC name -- definitional
        # equality, never name coincidence.
        if str(securable).count(".") == 2:
            table = node_id("data", "table", str(securable))
            if table in graph.nodes:
                graph.add_edge(Edge(_securable_id(str(securable)), "governs",
                                    table, {}, prov))


def _edges_rbac(graph: Graph, fact: Mapping[str, Any]) -> None:
    subject, prov = fact.get("subject") or {}, _prov(fact)
    principal = str(subject.get("principal") or "")
    scope = str(subject.get("scope") or "")
    if not principal or not scope:
        return
    asn = node_id("azure", "resource", f"roleAssignment:{principal}@{scope.lower()}")
    graph.add_edge(Edge(node_id("azure", "identity", principal), "has_role",
                        asn, {}, prov))
    if is_arm_id(scope):
        graph.add_edge(Edge(asn, "applies_to", _arm_node(scope), {}, prov))
    else:
        graph.add_unresolved({"reason": "assignment_scope_not_arm_id",
                              "fact": fact.get("id")})


def _edges_adls(graph: Graph, fact: Mapping[str, Any]) -> None:
    if fact["kind"] != "adls.account":
        return
    prov = _prov(fact)
    account_id = str((fact.get("subject") or {}).get("account_id") or "")
    if not is_arm_id(account_id):
        return
    name = parse_arm_id(account_id).name
    # A filesystem joins its storage account through the ARM id's own name
    # segment -- the id is explicit evidence, not a display-name lookup.
    for nid in sorted(graph.nodes):
        if name and nid.startswith(f"azure:filesystem:{name}/"):
            graph.add_edge(Edge(nid, "located_in", _arm_node(account_id), {}, prov))


def _edges_compute(graph: Graph, fact: Mapping[str, Any]) -> None:
    if fact["kind"] != "databricks.compute":
        return
    prov = _prov(fact)
    attrs = fact.get("attrs") or {}
    ws = str(attrs.get("workspace_id") or "")
    job_id = str(attrs.get("job_id") or "")
    if not (job_id and ws):
        return
    job = node_id("data", "job", f"databricks:{ws}/{job_id}")
    graph.add_edge(Edge(job, "runs_in", _ws_id(ws), {}, prov))
    cluster_id = str(attrs.get("cluster_id") or "")
    if cluster_id:
        cluster = node_id("data", "cluster", f"databricks:{ws}/{cluster_id}")
        if cluster in graph.nodes:
            graph.add_edge(Edge(job, "uses", cluster, {}, prov))
    notebook_path = str(attrs.get("notebook_path") or "")
    if notebook_path:
        nb = node_id("data", "notebook", notebook_path)
        if nb in graph.nodes:
            graph.add_edge(Edge(job, "executes", nb, {}, prov))


def _edges_notebook(graph: Graph, fact: Mapping[str, Any]) -> None:
    kind, subject = fact["kind"], fact.get("subject") or {}
    attrs = fact.get("attrs") or {}
    file = subject.get("file")
    if not file or kind == "notebook.analyzed":
        return
    prov = _prov(fact)
    nb = node_id("data", "notebook", str(file))
    if kind == "notebook.abfss_path":
        fs = _fs_id(str(attrs.get("url") or ""))
        if fs:
            graph.add_edge(Edge(nb, "accesses", fs, {}, prov))
    elif kind in ("notebook.uc_table", "notebook.write_table", "notebook.delta_op",
                  "notebook.sql_op"):
        table = str(attrs.get("table") or attrs.get("target") or "")
        if table.count(".") != 2:
            return
        tid = node_id("data", "table", table)
        if tid not in graph.nodes:
            return
        writes = kind == "notebook.write_table" or (
            kind in ("notebook.delta_op", "notebook.sql_op")
            and str(attrs.get("op", "")).upper() in _WRITE_OPS)
        graph.add_edge(Edge(nb, "writes" if writes else "reads", tid, {}, prov))


def add_case_access(graph: Graph, case: Mapping[str, Any], prov: Provenance) -> None:
    """Case-level edge: the case principal ``accesses`` the case target."""
    principal = str((case.get("principal") or {}).get("id") or "")
    target = case.get("target") or {}
    if not principal:
        return
    pid = _add(graph, node_id("azure", "identity", principal), "identity", "azure",
               prov, {"principal_type": (case.get("principal") or {}).get("type")})
    if target.get("kind") == "table" and target.get("table"):
        tid = _add(graph, node_id("data", "table", str(target["table"])), "table",
                   "data", prov, {"name": target["table"]})
        graph.add_edge(Edge(pid, "accesses", tid,
                            {"operation": case.get("operation")}, prov))
        return
    fs = _fs_id(str(target.get("url") or ""))
    if fs:
        _add(graph, fs, "filesystem", "azure", prov, {"url": target.get("url")})
        graph.add_edge(Edge(pid, "accesses", fs,
                            {"operation": case.get("operation")}, prov))


_NODE_EMITTERS = {
    "unity_catalog.": _nodes_uc,
    "azure_rbac.": _nodes_rbac,
    "adls.": _nodes_adls,
    "databricks.": _nodes_compute,
    "notebook.": _nodes_notebook,
}

_EDGE_EMITTERS = {
    "unity_catalog.": _edges_uc,
    "azure_rbac.": _edges_rbac,
    "adls.": _edges_adls,
    "databricks.": _edges_compute,
    "notebook.": _edges_notebook,
}


def _link_filesystem_hierarchy(graph: Graph) -> None:
    """``part_of`` between nested filesystem nodes (explicit path prefix)."""
    fs_ids = sorted(n for n in graph.nodes if n.startswith("azure:filesystem:"))
    for child in fs_ids:
        parents = [p for p in fs_ids
                   if p != child and child.startswith(p + "/")]
        if parents:
            prov = graph.nodes[child].provenance
            graph.add_edge(Edge(child, "part_of", max(parents, key=len), {}, prov))


def _as_dict(fact: object) -> dict[str, Any]:
    if isinstance(fact, Mapping):
        return dict(fact)
    to_dict = getattr(fact, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    raise TypeError(f"unsupported fact type: {type(fact).__name__}")


def build_access_graph(facts: list[object],
                       case: Mapping[str, Any] | None = None) -> Graph:
    """Facts -> access graph.  Deterministic; unknown kinds become unresolved."""
    dicts = [_as_dict(f) for f in facts]
    dicts.sort(key=lambda f: (str(f.get("kind")), str(f.get("id"))))
    graph = Graph()
    known: list[dict[str, Any]] = []
    for fact in dicts:
        kind = str(fact.get("kind") or "")
        emitter = next((fn for prefix, fn in _NODE_EMITTERS.items()
                        if kind.startswith(prefix)), None)
        if emitter is None:
            graph.add_unresolved({"reason": "unsupported_fact_kind", "kind": kind})
            continue
        known.append(fact)
        emitter(graph, fact)
    for fact in known:
        kind = str(fact.get("kind") or "")
        _EDGE_EMITTERS[next(p for p in _EDGE_EMITTERS if kind.startswith(p))](
            graph, fact)
    _link_filesystem_hierarchy(graph)
    if case is not None:
        sources = sorted({str((f.get("provenance") or {}).get("source"))
                          for f in dicts if (f.get("provenance") or {}).get("source")})
        add_case_access(graph, case,
                        Provenance("artifact", ",".join(sources) or "case.yaml"))
    graph.meta = {"kind": "access", "facts": len(dicts)}
    return graph


__all__ = ["ACCESS_RELATIONS", "add_case_access", "build_access_graph"]
