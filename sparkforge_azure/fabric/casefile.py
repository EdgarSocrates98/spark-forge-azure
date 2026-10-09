"""Case bundle loading for the Fabric diagnostic pipeline.

A bundle is a directory::

    case.yaml            -- name, principal, operation, target, expect?
    workspace.json       -- {id, name?, capacity_id, roles{principal->role},
                            identity{principal_id,type}}
    items.json           -- {items:[{id,type,workspace_id,display_name,...}]}
    lakehouse.json       -- {id, workspace_id, tables:[...], files:[...]}
    onelake_security.json-- {item_id: {roles:[{name,permissions,members,scopes}]}}
    shortcuts.json       -- {shortcuts:[{id,lakehouse_id,path,target{...},
                            auth{mode,connection_id|identity}}]}
    connections.json     -- {id: {auth_kind,target{...}}}
    capacity.json        -- {id,sku,state,workspaces:[...],metrics:{...},
                            events:[{type}]} — utilization/throttling evidence
    environment.json     -- {id,workspace_id,runtime{version},...}
    pipelines.json       -- {pipelines:[{id,workspace_id,activities:[...]}]}
    identity.json        -- entra principals {id: {...}}
    notebooks/           -- optional .py/.sql/.ipynb scanned by notebook_scan

Everything is data.  Secrets in connection payloads are dropped at the
extraction boundary (``collectors.redact``) — the bundle files stay
byte-identical, the Facts never carry them.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.adapters.upstream import UPSTREAM_ARTIFACT, UpstreamError, read_upstream_facts
from sparkforge_azure.facts.scan import varrer_source_files

ARTIFACT_NAMES = (
    "workspace", "capacity", "items", "lakehouse", "onelake_security",
    "shortcuts", "connections", "environment", "pipelines", "identity",
)
_SUFFIXES = (".json", ".yaml", ".yml")
NOTEBOOK_SUFFIXES = frozenset({".py", ".sql", ".ipynb"})

#: Layer -> bundle artifact that feeds it (evidence-path + unresolved maps).
LAYER_SOURCE = {
    "fabric_workspace": "workspace",
    "item_permission": "items",
    "onelake_security": "onelake_security",
    "lakehouse": "lakehouse",
    "shortcut": "shortcuts",
    "shortcut_auth": "shortcuts",
    "source_access": "connections",
    "spark_runtime": "environment",
    "spark_job": "items",
    "capacity": "capacity",
    "data_factory": "pipelines",
}


class CaseError(ValueError):
    """Bundle inválido ou ilegível. Surfaces traduzem para exit 2 / erro MCP."""


@dataclass
class CaseBundle:
    """Loaded bundle: case dict, artifact payloads, and the file each came from."""

    root: Path
    case: dict[str, Any]
    artifacts: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    notebook_files: list[Path] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    upstream_facts: list[dict[str, Any]] = field(default_factory=list)


def _load_payload(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise CaseError(f"artifact unreadable: {path.name}") from exc
    try:
        if path.suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except ValueError as exc:
        raise CaseError(f"artifact is not valid {path.suffix}: {path.name}") from exc


def load_bundle(root: str | Path) -> CaseBundle:
    root = Path(root)
    if not root.is_dir():
        raise CaseError(f"bundle directory not found: {root}")
    case_file = next((root / f"case{s}" for s in _SUFFIXES if (root / f"case{s}").is_file()),
                     None)
    if case_file is None:
        raise CaseError(f"bundle missing case.yaml: {root}")
    case = _load_payload(case_file)
    if not isinstance(case, Mapping):
        raise CaseError("case.yaml must be a mapping")
    for key in ("principal", "operation", "target"):
        if key not in case:
            raise CaseError(f"case.yaml missing required key: {key}")
    bundle = CaseBundle(root=root, case=dict(case),
                        sources={"case": case_file.name})
    for name in ARTIFACT_NAMES:
        path = next((root / f"{name}{s}" for s in _SUFFIXES
                     if (root / f"{name}{s}").is_file()), None)
        if path is None:
            continue
        payload = _load_payload(path)
        if not isinstance(payload, Mapping):
            raise CaseError(f"{path.name} must be a mapping")
        bundle.artifacts[name] = dict(payload)
        bundle.sources[name] = path.name

    upstream_doc = root / UPSTREAM_ARTIFACT
    if upstream_doc.is_file():
        try:
            bundle.upstream_facts = read_upstream_facts(upstream_doc)
        except UpstreamError as exc:
            raise CaseError(str(exc)) from exc
        bundle.sources["upstream"] = upstream_doc.name
    nb_dir = root / "notebooks"
    if nb_dir.is_dir():
        varredura = varrer_source_files(nb_dir, "*")
        bundle.notebook_files = [p for p in varredura.arquivos
                                 if p.suffix.lower() in NOTEBOOK_SUFFIXES]
        bundle.skipped = [{"path": p.relativo, "reason": p.razao}
                          for p in varredura.pulos]
    return bundle


__all__ = [
    "ARTIFACT_NAMES", "CaseBundle", "CaseError", "LAYER_SOURCE", "load_bundle",
]
