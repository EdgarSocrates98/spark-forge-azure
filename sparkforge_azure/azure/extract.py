"""Deterministic extractors: Azure access artifacts -> Facts.

Every extractor takes the decoded artifact payload plus a provenance dict and
returns Facts.  No judgement here -- Facts are anchored observations; the
governance engine and the rule catalog do the judging.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.findings.models import Fact, sort_facts

Prov = dict[str, Any]


def _p(prov: Prov, extractor: str) -> Prov:
    return {**prov, "extractor": extractor}


def extract_uc(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_uc")
    facts: list[Fact] = []
    for name, cred in sorted((payload.get("storage_credentials") or {}).items()):
        if not isinstance(cred, Mapping):
            continue
        facts.append(Fact(
            kind="unity_catalog.storage_credential",
            subject={"name": str(name)},
            attrs={k: v for k, v in cred.items()
                   if isinstance(v, (str, int, float, bool))},
            provenance=dict(prov)))
    for loc in payload.get("external_locations") or []:
        if not isinstance(loc, Mapping) or not loc.get("name"):
            continue
        facts.append(Fact(
            kind="unity_catalog.external_location",
            subject={"name": str(loc["name"])},
            attrs=dict(loc),
            provenance=dict(prov)))
    for name, cat in sorted((payload.get("catalogs") or {}).items()):
        attrs = dict(cat) if isinstance(cat, Mapping) else {}
        if str(attrs.get("isolation_mode", "OPEN")).upper() == "ISOLATED":
            workspaces = list(attrs.get("workspaces") or [])
            facts.append(Fact(
                kind="unity_catalog.binding",
                subject={"catalog": str(name)},
                attrs={"workspaces": workspaces,
                       "isolation_mode": "ISOLATED"},
                measures={"bound_workspaces": len(workspaces)},
                provenance=dict(prov)))
        facts.append(Fact(kind="unity_catalog.catalog", subject={"name": str(name)},
                          attrs=attrs, provenance=dict(prov)))
    for name, schema in sorted((payload.get("schemas") or {}).items()):
        facts.append(Fact(kind="unity_catalog.schema", subject={"name": str(name)},
                          attrs=dict(schema) if isinstance(schema, Mapping) else {},
                          provenance=dict(prov)))
    for name, tbl in sorted((payload.get("tables") or {}).items()):
        facts.append(Fact(kind="unity_catalog.table", subject={"name": str(name)},
                          attrs=dict(tbl) if isinstance(tbl, Mapping) else {},
                          provenance=dict(prov)))
    for g in payload.get("grants") or []:
        if not isinstance(g, Mapping) or not g.get("securable"):
            continue
        facts.append(Fact(
            kind="unity_catalog.grant",
            subject={"securable": str(g["securable"]),
                     "principal": str(g.get("principal", ""))},
            attrs={"privileges": list(g.get("privileges") or [])},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_rbac(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_rbac")
    facts = [
        Fact(kind="azure_rbac.assignment",
             subject={"principal": str(a.get("principal", "")),
                      "scope": str(a.get("scope", ""))},
             attrs={"role": str(a.get("role", "")),
                    **({"condition": True} if a.get("condition") else {}),
                    **({"condition_result": a["condition_result"]}
                       if "condition_result" in a else {})},
             provenance=dict(prov))
        for a in payload.get("assignments") or []
        if isinstance(a, Mapping)
    ]
    return sort_facts(facts)


def extract_adls(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_adls")
    facts: list[Fact] = []
    account = str(payload.get("account_id", ""))
    if account:
        facts.append(Fact(
            kind="adls.account", subject={"account_id": account},
            attrs={"hns": payload.get("hns")},
            provenance=dict(prov)))
    for path, acl in sorted((payload.get("acl") or {}).items()):
        if not isinstance(acl, Mapping):
            continue
        facts.append(Fact(
            kind="adls.acl",
            subject={"account_id": account, "path": str(path)},
            attrs={"owner": acl.get("owner"),
                   "owning_group": acl.get("owning_group"),
                   "entries": list(acl.get("entries") or [])},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_network(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_network")
    attrs = {k: v for k, v in payload.items()
             if isinstance(v, (str, int, float, bool, list))}
    return [Fact(kind="network.storage", subject={"target": "storage"},
                 attrs=attrs, provenance=prov)]


def extract_entra(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_entra")
    return sort_facts(
        Fact(kind="entra.principal", subject={"id": str(pid)},
             attrs=dict(info) if isinstance(info, Mapping) else {},
             provenance=dict(prov))
        for pid, info in sorted((payload.get("principals") or {}).items())
    )


def extract_compute(payload: Mapping[str, Any], provenance: Prov) -> list[Fact]:
    prov = _p(provenance, "extract_compute")
    attrs = {k: v for k, v in payload.items()
             if isinstance(v, (str, int, float, bool, list))}
    return [Fact(kind="databricks.compute", subject={"target": "job-compute"},
                 attrs=attrs, provenance=prov)]


_EXTRACTORS = {
    "unity_catalog": extract_uc,
    "rbac": extract_rbac,
    "adls": extract_adls,
    "network": extract_network,
    "entra": extract_entra,
    "compute": extract_compute,
}


def extract_all(artifacts: Mapping[str, Any],
                sources: Mapping[str, str]) -> list[Fact]:
    """Run every extractor whose artifact is present in the bundle."""
    facts: list[Fact] = []
    for name, payload in artifacts.items():
        extractor = _EXTRACTORS.get(name)
        if extractor is None or payload is None:
            continue
        prov = {"source": sources.get(name, name), "mode": "bundle",
                "observed_at": None}
        facts.extend(extractor(payload, prov))
    return sort_facts(facts)


__all__ = [
    "extract_adls", "extract_all", "extract_compute", "extract_entra",
    "extract_network", "extract_rbac", "extract_uc",
]
