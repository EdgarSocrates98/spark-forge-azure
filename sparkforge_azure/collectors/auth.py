"""Authentication support for read-only collectors (sections 178-179).

Supported credential kinds (all via ``azure-identity``, imported lazily):
DefaultAzureCredential, Azure CLI, Managed Identity, Service Principal
(secret read from the environment only) and Workload Identity.

Offline mode needs no auth at all: importing ``sparkforge_azure.collectors``
never imports an Azure SDK.  Only ``require_azure_identity()`` /
``get_credential()`` do, and they raise ``CollectorUnavailable`` with an
install hint when the ``azure`` extra is missing.
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType
from typing import Any

from sparkforge_azure.collectors.base import CollectorUnavailable

CREDENTIAL_KINDS: dict[str, str] = {
    "default": "DefaultAzureCredential",
    "cli": "AzureCliCredential",
    "managed_identity": "ManagedIdentityCredential",
    "service_principal": "ClientSecretCredential",
    "workload_identity": "WorkloadIdentityCredential",
}
_SP_ENV = ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")


def require_module(name: str, extra: str) -> ModuleType:
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise CollectorUnavailable(
            f"{name} is not installed; install the optional extra: "
            f"pip install 'sparkforge-azure[{extra}]'"
        ) from exc


def require_azure_identity() -> ModuleType:
    return require_module("azure.identity", "azure")


def describe_auth(kind: str = "default") -> dict[str, Any]:
    """Offline description of what a credential kind needs (no SDK import,
    never echoes secret values -- only whether variables are present)."""

    if kind not in CREDENTIAL_KINDS:
        raise ValueError(f"unknown credential kind: {kind!r}")
    needs: tuple[str, ...] = ()
    if kind == "service_principal":
        needs = _SP_ENV
    elif kind == "workload_identity":
        needs = ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_FEDERATED_TOKEN_FILE")
    return {
        "kind": kind,
        "class": CREDENTIAL_KINDS[kind],
        "env_required": list(needs),
        "env_present": {name: bool(os.environ.get(name)) for name in needs},
        "offline_supported": True,
    }


def get_credential(kind: str = "default", *, client_id: str | None = None) -> Any:
    """Build a credential lazily.  Secrets are never accepted as arguments."""

    if kind not in CREDENTIAL_KINDS:
        raise ValueError(f"unknown credential kind: {kind!r}")
    identity = require_azure_identity()
    cls = getattr(identity, CREDENTIAL_KINDS[kind])
    if kind == "service_principal":
        missing = [n for n in _SP_ENV if not os.environ.get(n)]
        if missing:
            raise CollectorUnavailable(f"service principal env missing: {', '.join(missing)}")
        return cls(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"],
        )
    if kind == "managed_identity" and client_id:
        return cls(client_id=client_id)
    return cls()


__all__ = [
    "CREDENTIAL_KINDS",
    "describe_auth",
    "get_credential",
    "require_azure_identity",
    "require_module",
]
