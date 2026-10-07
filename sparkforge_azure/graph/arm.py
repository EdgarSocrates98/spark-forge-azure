"""ARM resource id helpers: shape validation, parsing, kind mapping.

Composition in Graphfy is by explicit id.  These helpers validate the id SHAPE
(they never resolve anything against Azure) and map an ARM ``type`` to a
Graphfy azure-layer kind.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_SEGMENT = r"[^/\s?#]+"
GUID_RE = re.compile(rf"^{_GUID}$")
SUBSCRIPTION_RE = re.compile(rf"^/subscriptions/{_GUID}$", re.IGNORECASE)
RESOURCE_GROUP_RE = re.compile(
    rf"^/subscriptions/{_GUID}/resourceGroups/{_SEGMENT}$", re.IGNORECASE
)
RESOURCE_RE = re.compile(
    rf"^/subscriptions/{_GUID}/resourceGroups/{_SEGMENT}/providers/"
    rf"[A-Za-z][A-Za-z0-9]*(\.[A-Za-z][A-Za-z0-9]*)+"
    rf"(/[A-Za-z][A-Za-z0-9]*/{_SEGMENT})+$",
    re.IGNORECASE,
)
# Anything that looks like an ARM id inside free text / properties.
ARM_IN_TEXT_RE = re.compile(
    rf"/subscriptions/{_GUID}/resourceGroups/{_SEGMENT}/providers/[A-Za-z0-9.]+(?:/[^/\s\"'?#]+)+",
    re.IGNORECASE,
)
DATABRICKS_WORKSPACE_ID_RE = re.compile(r"^[0-9]{6,20}$")

KIND_BY_TYPE: dict[str, str] = {
    "microsoft.storage/storageaccounts": "storage_account",
    "microsoft.storage/storageaccounts/blobservices/containers": "filesystem",
    "microsoft.databricks/workspaces": "databricks_workspace",
    "microsoft.databricks/accessconnectors": "identity",
    "microsoft.datafactory/factories": "adf",
    "microsoft.fabric/capacities": "fabric_capacity",
    "microsoft.eventhub/namespaces": "event_hub",
    "microsoft.eventhub/namespaces/eventhubs": "event_hub",
    "microsoft.purview/accounts": "purview",
    "microsoft.keyvault/vaults": "key_vault",
    "microsoft.managedidentity/userassignedidentities": "identity",
    "microsoft.synapse/workspaces": "workspace",
    "microsoft.operationalinsights/workspaces": "workspace",
    "microsoft.machinelearningservices/workspaces": "workspace",
}


class ArmIdError(ValueError):
    """Value does not have the shape of an ARM id."""


@dataclass(frozen=True)
class ArmId:
    raw: str
    subscription_id: str
    resource_group: str | None
    provider_type: str | None
    name: str | None

    @property
    def normalized(self) -> str:
        return self.raw.strip().rstrip("/").lower()

    @property
    def subscription_scope(self) -> str:
        return f"/subscriptions/{self.subscription_id.lower()}"

    @property
    def resource_group_scope(self) -> str | None:
        if self.resource_group is None:
            return None
        return f"{self.subscription_scope}/resourcegroups/{self.resource_group.lower()}"


def is_arm_id(value: object) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip().rstrip("/")
    if ".." in v or "\\" in v:
        return False
    return bool(RESOURCE_RE.match(v) or RESOURCE_GROUP_RE.match(v) or SUBSCRIPTION_RE.match(v))


def parse_arm_id(value: str) -> ArmId:
    if not is_arm_id(value):
        raise ArmIdError(f"invalid ARM resource id: {value!r}")
    v = value.strip().rstrip("/")
    parts = v.split("/")[1:]
    # parts: subscriptions, <sub>, resourceGroups, <rg>, providers, <ns>, <type>, <name>, ...
    sub = parts[1]
    rg = parts[3] if len(parts) > 3 else None
    provider_type = None
    name = None
    if len(parts) > 5:
        ns = parts[5]
        rest = parts[6:]
        types = [rest[i] for i in range(0, len(rest), 2)]
        provider_type = "/".join([ns, *types]).lower()
        name = rest[-1]
    return ArmId(v, sub, rg, provider_type, name)


def kind_for_type(arm_type: str | None) -> str:
    if not arm_type:
        return "resource"
    t = arm_type.strip().lower()
    if t in KIND_BY_TYPE:
        return KIND_BY_TYPE[t]
    if t.startswith("microsoft.network/"):
        return "network"
    return "resource"


def kind_for_arm_id(value: str) -> str:
    parsed = parse_arm_id(value)
    if parsed.provider_type is None:
        return "resource_group" if parsed.resource_group else "subscription"
    return kind_for_type(parsed.provider_type)


__all__ = [
    "ARM_IN_TEXT_RE",
    "DATABRICKS_WORKSPACE_ID_RE",
    "GUID_RE",
    "KIND_BY_TYPE",
    "ArmId",
    "ArmIdError",
    "is_arm_id",
    "kind_for_arm_id",
    "kind_for_type",
    "parse_arm_id",
]
