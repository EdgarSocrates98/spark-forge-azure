"""Case bundle loading for the migration assessment pipeline.

A bundle is a directory::

    case.yaml            -- name, principal, operation, target, expect?
    estate.json          -- {adf_factories:[{id,name,location,
                            pipelines:[{id,name,activities:[{name,type,
                            depends_on,linked_service,dataset_refs,
                            parameters,expressions}]}],
                            datasets:[{id,name,type,linked_service,path,
                            format}], linked_services:[{id,name,type,
                            auth_kind,target}], triggers:[{id,name,type,
                            pipelines}], integration_runtimes:[{id,name,
                            kind,nodes,region}], global_parameters:[{name,
                            type}]}],
                            synapse_workspaces:[{id,name,
                            pipelines:[...same shape],
                            notebooks:[{id,name,path,spark_pool_id}],
                            spark_pools:[{id,name,node_size,node_count,
                            auto_pause,spark_version,libraries,
                            spark_configs}],
                            libraries:[{name,kind,version}],
                            spark_configs:[{key,value}],
                            lake_databases:[{id,name,tables:[{name,kind,
                            location,format}]}]}],
                            fabric_workspaces:[{id,name,
                            items:[{id,type,name}]}],
                            storage_accounts:[{id,name,kind,retirement,
                            format_hint}]}
    assessment.json      -- official Microsoft assessment export
                            {tool, assessed_at, results:[{asset_id,
                            asset_name, official_status, notes}]}
    environment.json     -- scope facts (tenant/subscription/region...)
    validation.json      -- post-migration evidence {results:[{asset_id,
                            dimension, metric, source_value,
                            target_value, verdict}]}
    notebooks/           -- Synapse notebook sources scanned for refactor
                            patterns (DATA_ONLY)

Everything is data.  Assessment exports and user-provided plans are
EXTERNAL_DATA — evidence, never authority.  Secrets (connection strings,
SAS, keys) are dropped at the extraction boundary (``collectors.redact``).
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.facts.scan import varrer_source_files

ARTIFACT_NAMES = (
    "estate", "assessment", "environment", "validation", "plan",
)
_SUFFIXES = (".json", ".yaml", ".yml")
NOTEBOOK_SUFFIXES = frozenset({".py", ".sql", ".ipynb", ".scala"})


class MigrationCaseError(ValueError):
    """Bundle inválido ou ilegível. Surfaces traduzem para exit 2 / erro MCP."""


@dataclass
class MigrationBundle:
    """Loaded bundle: case dict, artifact payloads, and file provenance."""

    root: Path
    case: dict[str, Any]
    artifacts: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    notebook_files: list[Path] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)


def _load_payload(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise MigrationCaseError(f"artifact unreadable: {path.name}") from exc
    try:
        if path.suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except ValueError as exc:
        raise MigrationCaseError(
            f"artifact is not valid {path.suffix}: {path.name}") from exc


def load_bundle(root: str | Path) -> MigrationBundle:
    root = Path(root)
    if not root.is_dir():
        raise MigrationCaseError(f"bundle directory not found: {root}")
    case_file = next((root / f"case{s}" for s in _SUFFIXES
                      if (root / f"case{s}").is_file()), None)
    if case_file is None:
        raise MigrationCaseError(f"bundle missing case.yaml: {root}")
    case = _load_payload(case_file)
    if not isinstance(case, Mapping):
        raise MigrationCaseError("case.yaml must be a mapping")
    for key in ("principal", "operation", "target"):
        if key not in case:
            raise MigrationCaseError(f"case.yaml missing required key: {key}")
    bundle = MigrationBundle(root=root, case=dict(case),
                             sources={"case": case_file.name})
    for name in ARTIFACT_NAMES:
        path = next((root / f"{name}{s}" for s in _SUFFIXES
                     if (root / f"{name}{s}").is_file()), None)
        if path is None:
            continue
        payload = _load_payload(path)
        if not isinstance(payload, Mapping):
            raise MigrationCaseError(f"{path.name} must be a mapping")
        bundle.artifacts[name] = dict(payload)
        bundle.sources[name] = path.name
    nb_dir = root / "notebooks"
    if nb_dir.is_dir():
        varredura = varrer_source_files(nb_dir, "*")
        bundle.notebook_files = [p for p in varredura.arquivos
                                 if p.suffix.lower() in NOTEBOOK_SUFFIXES]
        bundle.skipped = [{"path": p.relativo, "reason": p.razao}
                          for p in varredura.pulos]
    return bundle


__all__ = [
    "ARTIFACT_NAMES", "MigrationBundle", "MigrationCaseError", "load_bundle",
]
