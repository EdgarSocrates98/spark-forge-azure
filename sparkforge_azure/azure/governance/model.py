"""Access scenario: the declared, offline evidence for one access question.

An *access scenario* answers "can principal P perform operation O on target T,
and if not, which layer denies it?".  Every layer is optional evidence; a
missing layer is UNKNOWN, never ALLOW (unknown != zero, section 77).

Shape (JSON/YAML)::

    principal:  {id, type: user|group|service_principal|managed_identity,
                 mi_kind?: system_assigned|user_assigned, enabled?: bool,
                 groups?: [object ids]}
    operation:  read | write | list | delete
    target:     {kind: path|table|volume,
                 url?: abfss://<container>@<account>.dfs.core.windows.net/<path>,
                 table?: catalog.schema.table}
    compute?:   {workspace_id?, type: serverless|classic_vnet|public|unknown,
                 subnet_id?, egress_ip?, dns_resolves?: private|public|unknown}
    entra?:     {principals: {<id>: {enabled: bool, type: ...}}}
    rbac?:      {assignments: [{principal, role, scope, condition?, condition_result?}]}
    adls?:      {account_id: ARM id of the storage account, hns: bool,
                 acl: {"/": {owner, owning_group, entries: [...]}, "/dir": {...}}}
    network?:   {public_network_access: Enabled|Disabled, default_action: Allow|Deny,
                 bypass: [AzureServices], ip_rules: [...], vnet_rules: [subnet ids],
                 resource_instance_rules: [ARM ids], private_endpoint: bool}
    unity_catalog?: {grants: [{securable, principal, privileges: [...]}],
                 catalogs: {<name>: {isolation_mode: OPEN|ISOLATED, workspaces: [ids]}},
                 external_locations: [{name, url, credential, isolation_mode?, workspaces?}],
                 storage_credentials: {<name>: {access_connector_id, identity_id}}}

ACL entries: ``{type: user|group|mask|other, id?: object id, perms: "rwx"}``
where ``perms`` uses ``-`` for absent bits (``r-x``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sparkforge_azure.abfss import split_abfss

OPERATIONS = frozenset({"read", "write", "list", "delete"})
PRINCIPAL_TYPES = frozenset({"user", "group", "service_principal", "managed_identity"})


class Verdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    UNKNOWN = "unknown"  # evidence missing -- never treated as allow
    NOT_APPLICABLE = "not_applicable"


class ScenarioError(ValueError):
    """The scenario itself is malformed (exit 2), not a governance finding."""


@dataclass(frozen=True, slots=True)
class LayerResult:
    layer: str
    verdict: Verdict
    reason: str
    identity: str = ""
    evidence: tuple[str, ...] = ()  # fact ids
    knowledge_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"layer": self.layer, "verdict": self.verdict.value, "reason": self.reason,
                "identity": self.identity, "evidence": list(self.evidence),
                "knowledge_refs": list(self.knowledge_refs)}


@dataclass
class Scenario:
    principal: Mapping[str, Any]
    operation: str
    target: Mapping[str, Any]
    compute: Mapping[str, Any] = field(default_factory=dict)
    entra: Mapping[str, Any] | None = None
    rbac: Mapping[str, Any] | None = None
    adls: Mapping[str, Any] | None = None
    network: Mapping[str, Any] | None = None
    unity_catalog: Mapping[str, Any] | None = None
    name: str = ""

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Scenario:
        if not isinstance(raw, Mapping):
            raise ScenarioError("scenario must be a mapping")
        principal = raw.get("principal")
        if not isinstance(principal, Mapping) or not principal.get("id"):
            raise ScenarioError("principal.id is required")
        if principal.get("type") not in PRINCIPAL_TYPES:
            raise ScenarioError(f"principal.type must be one of {sorted(PRINCIPAL_TYPES)}")
        op = raw.get("operation")
        if op not in OPERATIONS:
            raise ScenarioError(f"operation must be one of {sorted(OPERATIONS)}")
        target = raw.get("target")
        if not isinstance(target, Mapping) or target.get("kind") not in {"path", "table",
                                                                          "volume"}:
            raise ScenarioError("target.kind must be path|table|volume")
        if target["kind"] == "path" and not str(target.get("url", "")).startswith("abfss://"):
            raise ScenarioError("path targets need an abfss:// url")
        if target["kind"] == "table" and str(target.get("table", "")).count(".") != 2:
            raise ScenarioError("table targets need catalog.schema.table")
        return cls(
            principal=principal, operation=op, target=target,
            compute=raw.get("compute") or {}, entra=raw.get("entra"), rbac=raw.get("rbac"),
            adls=raw.get("adls"), network=raw.get("network"),
            unity_catalog=raw.get("unity_catalog"), name=str(raw.get("name", "")),
        )


def parse_abfss(url: str) -> tuple[str, str, str]:
    """``abfss://container@account.dfs.core.windows.net/a/b`` -> (account, container, /a/b)."""
    parts = split_abfss(url)
    if parts is None:
        raise ScenarioError(f"not an abfss url: {url}")
    return parts
