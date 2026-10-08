"""Deterministic extractors: Fabric artifacts -> Facts (SDD FABRIC_CORE).

Same contract as ``azure.extract``: every extractor takes the decoded
artifact payload plus a provenance dict and returns Facts.  No judgement —
Facts are anchored observations; the Fabric diagnosis engine and the rule
catalog do the judging.

Fabric IDs are official GUIDs carried in ``id`` keys.  A display name is
recorded as an attr but is never a subject key — name equality does not
identify a resource.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.fabric.model import ITEM_TYPES
from sparkforge_azure.findings.models import Fact, sort_facts

Prov = dict[str, Any]


def _p(prov: Prov, extractor: str) -> Prov:
    return {**prov, "extractor": extractor}


def extract_workspace(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_workspace")
    facts: list[Fact] = []
    wid = str(payload.get("id", ""))
    if not wid:
        return facts
    attrs = {"display_name": payload.get("name"),
             "capacity_id": payload.get("capacity_id"),
             "region": payload.get("region")}
    facts.append(Fact(kind="fabric.workspace",
                      subject={"workspace_id": wid},
                      attrs={k: v for k, v in attrs.items() if v is not None},
                      provenance=dict(prov)))
    cap = str(payload.get("capacity_id", ""))
    if cap:
        facts.append(Fact(kind="fabric.workspace_capacity",
                          subject={"workspace_id": wid, "capacity_id": cap},
                          attrs={}, provenance=dict(prov)))
    for principal, role in sorted((payload.get("roles") or {}).items()):
        facts.append(Fact(kind="fabric.workspace_role",
                          subject={"workspace_id": wid,
                                   "principal": str(principal)},
                          attrs={"role": str(role)},
                          provenance=dict(prov)))
    # Shortcut targets may live in *other* workspaces; the artifact carries
    # their role maps under peer_workspaces so passthrough can be evaluated.
    for peer_id, peer in sorted((payload.get("peer_workspaces") or {}).items()):
        if not isinstance(peer, Mapping):
            continue
        for principal, role in sorted((peer.get("roles") or {}).items()):
            facts.append(Fact(kind="fabric.workspace_role",
                              subject={"workspace_id": str(peer_id),
                                       "principal": str(principal)},
                              attrs={"role": str(role), "peer": True},
                              provenance=dict(prov)))
    identity = payload.get("identity")
    if isinstance(identity, Mapping):
        facts.append(Fact(
            kind="fabric.workspace_identity",
            subject={"workspace_id": wid,
                     "principal_id": str(identity.get("principal_id", ""))},
            attrs={k: v for k, v in identity.items()
                   if isinstance(v, (str, bool, int))},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_items(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_items")
    facts: list[Fact] = []
    for item in payload.get("items") or []:
        if not isinstance(item, Mapping) or not item.get("id"):
            continue
        iid = str(item["id"])
        itype = str(item.get("type") or "")
        attrs = {"type": itype,
                 "workspace_id": str(item.get("workspace_id", "")),
                 "display_name": item.get("display_name")}
        if item.get("permissions"):
            attrs["permissions"] = item["permissions"]
        # SparkJobDefinition surface (current docs): default lakehouse,
        # environment, retry policy — carried when the export declares them.
        for key in ("main_file", "default_lakehouse_id", "environment_id",
                    "runtime"):
            if item.get(key) is not None:
                attrs[key] = str(item[key])
        retry = item.get("retry_policy")
        if isinstance(retry, Mapping):
            attrs["retry_policy_enabled"] = bool(retry.get("enabled", True))
            attrs["retry_max"] = retry.get("max_attempts")
            attrs["retry_idempotent_evidence"] = bool(
                retry.get("idempotent_evidence"))
        kind = {
            "Lakehouse": "fabric.lakehouse",
            "Notebook": "fabric.notebook",
            "SparkJobDefinition": "fabric.spark_job",
            "Environment": "fabric.environment",
            "DataPipeline": "fabric.pipeline",
        }.get(itype, "fabric.item")
        subject = {"item_id": iid}
        if kind == "fabric.item":
            subject["type"] = itype
        facts.append(Fact(kind=kind, subject=subject,
                          attrs={k: v for k, v in attrs.items()
                                 if v is not None},
                          measures={},
                          provenance=dict(prov)))
        # Generic item fact too so `items` enumeration never loses coverage
        # when a typed kind exists.
        if kind != "fabric.item":
            facts.append(Fact(kind="fabric.item",
                              subject={"item_id": iid, "type": itype},
                              attrs={k: v for k, v in attrs.items()
                                     if v is not None},
                              provenance=dict(prov)))
    return sort_facts(facts)


def extract_lakehouse(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_lakehouse")
    facts: list[Fact] = []
    lid = str(payload.get("id", ""))
    wid = str(payload.get("workspace_id", ""))
    if not lid:
        return facts
    facts.append(Fact(kind="fabric.lakehouse",
                      subject={"item_id": lid},
                      attrs={"workspace_id": wid,
                             "display_name": payload.get("name")},
                      provenance=dict(prov)))
    for t in payload.get("tables") or []:
        tname = t.get("name") if isinstance(t, Mapping) else t
        if not tname:
            continue
        facts.append(Fact(kind="onelake.table",
                          subject={"lakehouse_id": lid, "name": str(tname)},
                          attrs=dict(t) if isinstance(t, Mapping) else {},
                          provenance=dict(prov)))
    for p in payload.get("files") or []:
        relpath = p.get("path") if isinstance(p, Mapping) else p
        if not relpath:
            continue
        facts.append(Fact(kind="onelake.path",
                          subject={"item_id": lid, "path": str(relpath)},
                          attrs=dict(p) if isinstance(p, Mapping) else {},
                          provenance=dict(prov)))
    return sort_facts(facts)


def extract_onelake_security(payload: Mapping[str, Any],
                             provenance: Prov) -> list[Fact]:
    """OneLake security roles per item (grant-only; deny is not modeled)."""
    prov = _p(provenance, "extract_onelake_security")
    facts: list[Fact] = []
    for item_id, spec in sorted(payload.items()):
        if not isinstance(spec, Mapping):
            continue
        for role in spec.get("roles") or []:
            if not isinstance(role, Mapping) or not role.get("name"):
                continue
            members = [
                m for m in (role.get("members") or []) if isinstance(m, str)]
            facts.append(Fact(
                kind="onelake.security_role",
                subject={"item_id": str(item_id),
                         "role": str(role["name"])},
                attrs={
                    "permissions": [
                        str(x) for x in (role.get("permissions") or [])],
                    "members": members,
                    "scopes": list(role.get("scopes") or []),
                    # Current OneLake roles only grant; deny does not exist.
                    "grant_model": True,
                },
                provenance=dict(prov)))
    return sort_facts(facts)


def extract_shortcuts(payload: Mapping[str, Any],
                      provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_shortcuts")
    facts: list[Fact] = []
    for sc in payload.get("shortcuts") or []:
        if not isinstance(sc, Mapping) or not sc.get("id"):
            continue
        auth = sc.get("auth") if isinstance(sc.get("auth"), Mapping) else {}
        target = sc.get("target") if isinstance(sc.get("target"), Mapping) else {}
        facts.append(Fact(
            kind="fabric.shortcut",
            subject={"shortcut_id": str(sc["id"]),
                     "lakehouse_id": str(sc.get("lakehouse_id", ""))},
            attrs={
                "path": str(sc.get("path", "")),
                "auth_mode": str(auth.get("mode", "")),
                "connection_id": str(auth.get("connection_id", "")),
                "workspace_identity": bool(auth.get("workspace_identity")),
                "target_kind": str(target.get("kind", "")),
                "target_workspace_id": str(target.get("workspace_id", "")),
                "target_item_id": str(target.get("item_id", "")),
                "target_url": str(target.get("url", "")),
                "target_tenant_id": str(target.get("tenant_id", "")),
            },
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_connections(payload: Mapping[str, Any],
                        provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_connections")
    facts = [
        Fact(kind="fabric.connection",
             subject={"connection_id": str(cid)},
             attrs={k: v for k, v in conn.items()
                    if isinstance(v, (str, bool, int))},
             provenance=dict(prov))
        for cid, conn in sorted(payload.items())
        if isinstance(conn, Mapping)
    ]
    return sort_facts(facts)


def extract_capacity(payload: Mapping[str, Any],
                     provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_capacity")
    facts: list[Fact] = []
    cid = str(payload.get("id", ""))
    if not cid:
        return facts
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), Mapping) else {}
    events = [str(e.get("type", "")) for e in (payload.get("events") or [])
              if isinstance(e, Mapping)]
    attrs = {"sku": payload.get("sku"), "state": payload.get("state")}
    attrs.update({f"metric_{k}": v for k, v in metrics.items()
                  if isinstance(v, (int, float, str, bool))})
    facts.append(Fact(kind="fabric.capacity",
                      subject={"capacity_id": cid},
                      attrs={k: v for k, v in attrs.items() if v is not None},
                      measures={"throttling_events": sum(
                          1 for e in events if "limit" in e.lower()
                          or "throttle" in e.lower())},
                      provenance=dict(prov)))
    for ev in payload.get("events") or []:
        if not isinstance(ev, Mapping) or not ev.get("type"):
            continue
        facts.append(Fact(kind="fabric.capacity_event",
                          subject={"capacity_id": cid,
                                   "type": str(ev["type"])},
                          attrs={k: v for k, v in ev.items()
                                 if isinstance(v, (str, int, float, bool))},
                          provenance=dict(prov)))
    for wid in payload.get("workspaces") or []:
        facts.append(Fact(kind="fabric.workspace_capacity",
                          subject={"workspace_id": str(wid),
                                   "capacity_id": cid},
                          attrs={}, provenance=dict(prov)))
    return sort_facts(facts)


def extract_environment(payload: Mapping[str, Any],
                        provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_environment")
    eid = str(payload.get("id", ""))
    if not eid:
        return []
    runtime = payload.get("runtime") if isinstance(payload.get("runtime"), Mapping) else {}
    return [Fact(kind="fabric.environment",
                 subject={"item_id": eid},
                 attrs={
                     "workspace_id": str(payload.get("workspace_id", "")),
                     "display_name": payload.get("name"),
                     "runtime_version": str(runtime.get("version", "")),
                     "spark_version": str(runtime.get("spark", "")),
                     "python_version": str(runtime.get("python", "")),
                     "libraries": len(payload.get("libraries") or []),
                 },
                 provenance=dict(prov))]


def extract_pipelines(payload: Mapping[str, Any],
                      provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_pipelines")
    facts: list[Fact] = []
    for pipe in payload.get("pipelines") or []:
        if not isinstance(pipe, Mapping) or not pipe.get("id"):
            continue
        pid = str(pipe["id"])
        facts.append(Fact(kind="fabric.pipeline",
                          subject={"item_id": pid},
                          attrs={"workspace_id": str(pipe.get("workspace_id", "")),
                                 "display_name": pipe.get("name")},
                          provenance=dict(prov)))
        for act in pipe.get("activities") or []:
            if not isinstance(act, Mapping) or not act.get("name"):
                continue
            facts.append(Fact(
                kind="fabric.pipeline_activity",
                subject={"pipeline_id": pid, "name": str(act["name"])},
                attrs={k: v for k, v in act.items()
                       if isinstance(v, (str, int, float, bool))},
                provenance=dict(prov)))
    return sort_facts(facts)


def extract_identity(payload: Mapping[str, Any],
                     provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_identity")
    return sort_facts(
        Fact(kind="entra.principal", subject={"id": str(pid)},
             attrs=dict(info) if isinstance(info, Mapping) else {},
             provenance=dict(prov))
        for pid, info in sorted((payload.get("principals") or {}).items())
    )


_EXTRACTORS = {
    "workspace": extract_workspace,
    "capacity": extract_capacity,
    "items": extract_items,
    "lakehouse": extract_lakehouse,
    "onelake_security": extract_onelake_security,
    "shortcuts": extract_shortcuts,
    "connections": extract_connections,
    "environment": extract_environment,
    "pipelines": extract_pipelines,
    "identity": extract_identity,
}

#: Keys that identify the environment the evidence came from.  Same contract
#: as ``azure.extract._ENV_KEYS`` — disagreement across artifacts is a
#: cross_environment finding, never silently merged.
_ENV_KEYS = ("tenant_id", "capacity_id", "workspace_id", "subscription_id")


def _env_values(value: Any, key: str, out: set[str]) -> None:
    if isinstance(value, Mapping):
        for k, v in value.items():
            if isinstance(k, str) and k.lower() == key and isinstance(v, str) and v:
                out.add(v.lower())
            _env_values(v, key, out)
    elif isinstance(value, list):
        for item in value:
            _env_values(item, key, out)


def extract_env(artifacts: Mapping[str, Any],
                sources: Mapping[str, str]) -> list[Fact]:
    facts: list[Fact] = []
    for name, payload in sorted(artifacts.items()):
        if not isinstance(payload, Mapping):
            continue
        prov = {"source": sources.get(name, name), "mode": "bundle",
                "observed_at": None, "extractor": "extract_env"}
        for key in _ENV_KEYS:
            found: set[str] = set()
            _env_values(payload, key, found)
            for value in sorted(found):
                facts.append(Fact(
                    kind="environment.scope",
                    subject={"source": sources.get(name, name), "key": key,
                             "value": value},
                    attrs={"key": key, "value": value},
                    provenance=dict(prov)))
    return facts


def extract_all(artifacts: Mapping[str, Any],
                sources: Mapping[str, str]) -> list[Fact]:
    """Run every extractor whose artifact is present.

    Artifacts are redacted at the extraction boundary (same contract as the
    access vertical): bundle files stay byte-identical on disk, but Facts
    never carry secret material.
    """
    from sparkforge_azure.collectors.redact import redact

    facts: list[Fact] = []
    for name, payload in artifacts.items():
        extractor = _EXTRACTORS.get(name)
        if extractor is None or payload is None:
            continue
        prov = {"source": sources.get(name, name), "mode": "bundle",
                "observed_at": None}
        facts.extend(extractor(redact(payload), prov))
    facts.extend(extract_env(artifacts, sources))
    return sort_facts(facts)


__all__ = [
    "extract_all", "extract_capacity", "extract_connections", "extract_env",
    "extract_environment", "extract_identity", "extract_items",
    "extract_lakehouse", "extract_onelake_security", "extract_pipelines",
    "extract_shortcuts", "extract_workspace", "ITEM_TYPES",
]
