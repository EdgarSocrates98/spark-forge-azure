"""Deterministic evaluation of each governance layer.

Sources (retrieved 2026-10-06, see docs/research/azure_sources_2026-10-06.md):

* ADLS Gen2 access control model -- RBAC is evaluated first; with a data-plane
  role and no ABAC condition access is granted and ACLs are NOT evaluated; ACLs
  cannot restrict what RBAC granted.  Without a data role, ACLs decide.
  https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model
* ADLS ACL semantics -- traversal needs execute (x) on every ancestor directory;
  read file needs r on the file; create/delete needs w+x on the parent; list
  needs r+x on the directory; the mask caps named users and all groups.
  https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control
* Unity Catalog -- workspace-catalog binding supersedes privilege grants;
  WRITE FILES without READ FILES on an external location yields PERMISSION_DENIED;
  storage is reached through the storage credential's access connector managed
  identity, not the end user.
  https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/securable-objects
  https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/manage-external-locations
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sparkforge_azure.azure.governance.model import LayerResult, Verdict, parse_abfss

K_ADLS = "azure.adls.acl-rbac"
K_UC = "azure.unity-catalog.troubleshooting-external-locations"
K_NET = "azure.network.private-link-dns"
K_ENTRA = "azure.identity.entra-managed-identity"

# Data-plane roles and what they allow (control-plane roles such as Owner,
# Contributor or Storage Account Contributor grant NO data access by RBAC).
DATA_ROLES: dict[str, frozenset[str]] = {
    "Storage Blob Data Owner": frozenset({"read", "write", "list", "delete"}),
    "Storage Blob Data Contributor": frozenset({"read", "write", "list", "delete"}),
    "Storage Blob Data Reader": frozenset({"read", "list"}),
}
CONTROL_PLANE_ROLES = frozenset({"Owner", "Contributor", "Reader", "Storage Account Contributor",
                                 "User Access Administrator"})


def _scope_covers(scope: str, target_scope: str) -> bool:
    s, t = scope.rstrip("/").lower(), target_scope.rstrip("/").lower()
    return t == s or t.startswith(s + "/")


def container_scope(account_id: str, container: str) -> str:
    return f"{account_id.rstrip('/')}/blobServices/default/containers/{container}"


# --------------------------------------------------------------------- Entra
def entra_layer(entra: Mapping[str, Any] | None, identity: str) -> LayerResult:
    if not entra:
        return LayerResult("entra", Verdict.UNKNOWN, "no Entra evidence for identity",
                           identity, knowledge_refs=(K_ENTRA,))
    info = (entra.get("principals") or {}).get(identity)
    if info is None:
        return LayerResult("entra", Verdict.DENY, "identity not found in tenant evidence",
                           identity, knowledge_refs=(K_ENTRA,))
    if info.get("enabled") is False:
        return LayerResult("entra", Verdict.DENY, "identity disabled", identity,
                           knowledge_refs=(K_ENTRA,))
    if info.get("enabled") is None:
        return LayerResult("entra", Verdict.UNKNOWN, "enabled state not observed", identity,
                           knowledge_refs=(K_ENTRA,))
    return LayerResult("entra", Verdict.ALLOW, "identity exists and is enabled", identity,
                       knowledge_refs=(K_ENTRA,))


# ---------------------------------------------------------------------- RBAC
def rbac_layer(rbac: Mapping[str, Any] | None, identity: str, groups: Sequence[str],
               target_scope: str, operation: str) -> tuple[LayerResult, dict[str, Any]]:
    """Returns the layer verdict and a detail dict used for conflict classification.

    ALLOW here means "RBAC grants the data operation" (ACL will not be consulted).
    DENY is never produced by RBAC alone: no data role means "fall through to ACL".
    """
    detail: dict[str, Any] = {"data_roles": [], "control_roles": [], "conditional": []}
    if rbac is None:
        return LayerResult("rbac", Verdict.UNKNOWN, "no role-assignment evidence", identity,
                           knowledge_refs=(K_ADLS,)), detail
    ids = {identity, *groups}
    for a in rbac.get("assignments") or []:
        if a.get("principal") not in ids or not _scope_covers(str(a.get("scope", "")),
                                                              target_scope):
            continue
        role = str(a.get("role", ""))
        if role in DATA_ROLES and operation in DATA_ROLES[role]:
            if a.get("condition"):
                detail["conditional"].append(a)
            else:
                detail["data_roles"].append(role)
        elif role in CONTROL_PLANE_ROLES:
            detail["control_roles"].append(role)
    if detail["data_roles"]:
        return LayerResult("rbac", Verdict.ALLOW,
                           f"data-plane role grants {operation}: "
                           f"{sorted(set(detail['data_roles']))}",
                           identity, knowledge_refs=(K_ADLS,)), detail
    for a in detail["conditional"]:
        result = a.get("condition_result")
        if result is True:
            return LayerResult("rbac", Verdict.ALLOW, "ABAC condition evaluated true",
                               identity, knowledge_refs=(K_ADLS,)), detail
        if result is None:
            return LayerResult("rbac", Verdict.UNKNOWN,
                               "ABAC condition present but its result was not observed",
                               identity, knowledge_refs=(K_ADLS,)), detail
    reason = "no data-plane role at target scope; ACL decides"
    if detail["control_roles"]:
        reason = (f"only control-plane roles {sorted(set(detail['control_roles']))} "
                  "(no data access); ACL decides")
    return LayerResult("rbac", Verdict.NOT_APPLICABLE, reason, identity,
                       knowledge_refs=(K_ADLS,)), detail


# ----------------------------------------------------------------------- ACL
def _bits(perms: str) -> set[str]:
    return {c for c in perms if c in "rwx"}


def _effective(acl: Mapping[str, Any], identity: str, groups: Sequence[str]) -> set[str] | None:
    """POSIX-style effective permissions; None when the ACL itself was not observed."""
    if not acl:
        return None
    entries = acl.get("entries") or []
    mask = next((_bits(e["perms"]) for e in entries if e.get("type") == "mask"), None)

    def masked(p: set[str]) -> set[str]:
        return p & mask if mask is not None else p

    if acl.get("owner") == identity:
        owner = next((e for e in entries if e.get("type") == "user" and not e.get("id")), None)
        return _bits(owner["perms"]) if owner else {"r", "w", "x"}
    named = next((e for e in entries if e.get("type") == "user" and e.get("id") == identity),
                 None)
    if named:
        return masked(_bits(named["perms"]))
    member = set(groups)
    group_perms: list[set[str]] = []
    if acl.get("owning_group") in member:
        og = next((e for e in entries if e.get("type") == "group" and not e.get("id")), None)
        if og:
            group_perms.append(_bits(og["perms"]))
    group_perms += [_bits(e["perms"]) for e in entries
                    if e.get("type") == "group" and e.get("id") in member]
    if group_perms:
        return masked(set().union(*group_perms))
    other = next((e for e in entries if e.get("type") == "other"), None)
    return _bits(other["perms"]) if other else set()


def _ancestors(path: str) -> list[str]:
    parts = [p for p in path.strip("/").split("/") if p]
    out = ["/"]
    for i in range(1, len(parts)):
        out.append("/" + "/".join(parts[:i]))
    return out


def acl_layer(adls: Mapping[str, Any] | None, identity: str, groups: Sequence[str], path: str,
              operation: str) -> LayerResult:
    if not adls or "acl" not in adls:
        return LayerResult("adls_acl", Verdict.UNKNOWN, "no ACL evidence", identity,
                           knowledge_refs=(K_ADLS,))
    if adls.get("hns") is False:
        return LayerResult("adls_acl", Verdict.NOT_APPLICABLE,
                           "account has no hierarchical namespace: ACLs do not exist", identity,
                           knowledge_refs=(K_ADLS,))
    acls: Mapping[str, Any] = adls["acl"]
    ancestors = _ancestors(path)
    if operation in {"write", "delete"}:
        need = {path.rsplit("/", 1)[0] or "/": {"w", "x"}}
        trav = ancestors[:-1] if len(ancestors) > 1 else []
    elif operation == "list":
        need = {path: {"r", "x"}}
        trav = ancestors
    else:  # read
        need = {path: {"r"}}
        trav = ancestors
    checks = [(a, {"x"}) for a in trav if a not in need] + list(need.items())
    for p, required in checks:
        eff = _effective(acls.get(p) or {}, identity, groups)
        if eff is None:
            return LayerResult("adls_acl", Verdict.UNKNOWN, f"ACL of {p} not observed", identity,
                               knowledge_refs=(K_ADLS,))
        missing = required - eff
        if missing:
            return LayerResult("adls_acl", Verdict.DENY,
                               f"ACL on {p} lacks {''.join(sorted(missing))} for {operation}",
                               identity, knowledge_refs=(K_ADLS,))
    return LayerResult("adls_acl", Verdict.ALLOW, f"ACL grants {operation} along {path}",
                       identity, knowledge_refs=(K_ADLS,))


# ------------------------------------------------------------------- Network
def network_layer(net: Mapping[str, Any] | None, compute: Mapping[str, Any],
                  identity_resource: str = "") -> LayerResult:
    if net is None:
        return LayerResult("network", Verdict.UNKNOWN, "no storage network evidence",
                           knowledge_refs=(K_NET,))
    ctype = compute.get("type", "unknown")
    if net.get("public_network_access") == "Disabled":
        if not net.get("private_endpoint"):
            return LayerResult("network", Verdict.DENY,
                               "public access disabled and no private endpoint",
                               knowledge_refs=(K_NET,))
        dns = compute.get("dns_resolves", "unknown")
        if dns == "public":
            return LayerResult("network", Verdict.DENY,
                               "private endpoint exists but storage FQDN resolves to a public "
                               "address from the compute (private DNS zone not linked)",
                               knowledge_refs=(K_NET,))
        if dns == "private" and ctype in {"classic_vnet", "serverless"}:
            return LayerResult("network", Verdict.ALLOW,
                               "reached through private endpoint (DNS resolves private)",
                               knowledge_refs=(K_NET,))
        return LayerResult("network", Verdict.UNKNOWN,
                           "private endpoint path not observed from this compute",
                           knowledge_refs=(K_NET,))
    if net.get("default_action", "Allow") == "Allow":
        return LayerResult("network", Verdict.ALLOW, "storage firewall default action Allow",
                           knowledge_refs=(K_NET,))
    if identity_resource and identity_resource in (net.get("resource_instance_rules") or []):
        return LayerResult("network", Verdict.ALLOW,
                           "access connector listed under resource instance rules",
                           knowledge_refs=(K_NET,))
    if compute.get("subnet_id") and compute["subnet_id"] in (net.get("vnet_rules") or []):
        return LayerResult("network", Verdict.ALLOW, "compute subnet allowed by firewall",
                           knowledge_refs=(K_NET,))
    if compute.get("egress_ip") and compute["egress_ip"] in (net.get("ip_rules") or []):
        return LayerResult("network", Verdict.ALLOW, "compute egress IP allowed by firewall",
                           knowledge_refs=(K_NET,))
    if ctype == "unknown":
        return LayerResult("network", Verdict.UNKNOWN,
                           "firewall denies by default and the compute origin is unknown",
                           knowledge_refs=(K_NET,))
    return LayerResult("network", Verdict.DENY,
                       "storage firewall default Deny and no rule matches the caller "
                       "(subnet, IP or resource instance)", knowledge_refs=(K_NET,))


# ------------------------------------------------------------- Unity Catalog
_PRIV_ALL = "ALL PRIVILEGES"


def _privs(uc: Mapping[str, Any], securable: str, ids: set[str]) -> set[str]:
    out: set[str] = set()
    for g in uc.get("grants") or []:
        if g.get("securable") == securable and g.get("principal") in ids:
            out |= {str(p).upper() for p in g.get("privileges") or []}
    return out


def _has(privs: set[str], needed: str) -> bool:
    return needed in privs or _PRIV_ALL in privs or "OWNER" in privs


def uc_binding_layer(uc: Mapping[str, Any], catalog: str | None,
                     location: Mapping[str, Any] | None, workspace_id: str | None) -> LayerResult:
    obj = None
    label = ""
    if catalog is not None:
        obj, label = (uc.get("catalogs") or {}).get(catalog), f"catalog {catalog}"
    elif location is not None:
        obj, label = location, f"external location {location.get('name')}"
    if obj is None:
        return LayerResult("uc_binding", Verdict.UNKNOWN, f"binding of {label or 'object'} "
                           "not observed", knowledge_refs=(K_UC,))
    if str(obj.get("isolation_mode", "OPEN")).upper() != "ISOLATED":
        return LayerResult("uc_binding", Verdict.ALLOW, f"{label} is OPEN to all workspaces",
                           knowledge_refs=(K_UC,))
    if not workspace_id:
        return LayerResult("uc_binding", Verdict.UNKNOWN,
                           f"{label} is ISOLATED and caller workspace is unknown",
                           knowledge_refs=(K_UC,))
    if str(workspace_id) in {str(w) for w in obj.get("workspaces") or []}:
        return LayerResult("uc_binding", Verdict.ALLOW, f"workspace bound to {label}",
                           knowledge_refs=(K_UC,))
    return LayerResult("uc_binding", Verdict.DENY,
                       f"{label} is ISOLATED and workspace {workspace_id} is not bound "
                       "(binding supersedes grants)", knowledge_refs=(K_UC,))


def uc_privilege_layer(uc: Mapping[str, Any], identity: str, groups: Sequence[str],
                       target: Mapping[str, Any], operation: str,
                       location: Mapping[str, Any] | None) -> LayerResult:
    ids = {identity, *groups}
    if target["kind"] == "table":
        cat, sch, _tbl = str(target["table"]).split(".")
        need = [("USE CATALOG", cat), ("USE SCHEMA", f"{cat}.{sch}"),
                ("SELECT" if operation in {"read", "list"} else "MODIFY", target["table"])]
    else:
        if location is None:
            return LayerResult("uc_privileges", Verdict.DENY,
                               "no external location covers the target url", identity,
                               knowledge_refs=(K_UC,))
        loc = f"external_location:{location['name']}"
        if operation in {"write", "delete"}:
            need = [("READ FILES", loc), ("WRITE FILES", loc)]
        else:
            need = [("READ FILES", loc)]
    missing = [f"{p} on {s}" for p, s in need if not _has(_privs(uc, s, ids), p)]
    if missing:
        hint = ""
        if any(m.startswith("READ FILES") for m in missing) and operation == "write":
            hint = " (WRITE FILES without READ FILES yields PERMISSION_DENIED)"
        return LayerResult("uc_privileges", Verdict.DENY, "missing " + ", ".join(missing) + hint,
                           identity, knowledge_refs=(K_UC,))
    return LayerResult("uc_privileges", Verdict.ALLOW,
                       "privileges present: " + ", ".join(p for p, _ in need), identity,
                       knowledge_refs=(K_UC,))


def covering_location(uc: Mapping[str, Any], url: str) -> Mapping[str, Any] | None:
    """Longest-prefix external location covering ``url``."""
    best = None
    for loc in uc.get("external_locations") or []:
        u = str(loc.get("url", "")).rstrip("/")
        if url.rstrip("/") == u or url.startswith(u + "/"):
            if best is None or len(u) > len(str(best.get("url", "")).rstrip("/")):
                best = loc
    return best


def storage_identity(uc: Mapping[str, Any], location: Mapping[str, Any] | None) -> tuple[str, str]:
    """(identity object id, access connector ARM id) behind a location's credential."""
    if location is None:
        return "", ""
    cred = (uc.get("storage_credentials") or {}).get(location.get("credential", ""))
    if not cred:
        return "", ""
    return str(cred.get("identity_id", "")), str(cred.get("access_connector_id", ""))


__all__ = [
    "CONTROL_PLANE_ROLES", "DATA_ROLES", "acl_layer", "container_scope", "covering_location",
    "entra_layer", "network_layer", "parse_abfss", "rbac_layer", "storage_identity",
    "uc_binding_layer", "uc_privilege_layer",
]
