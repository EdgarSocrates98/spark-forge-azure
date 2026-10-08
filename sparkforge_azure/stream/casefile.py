"""Case bundle loading for the streaming diagnostic pipeline.

A bundle is a directory::

    case.yaml            -- name, principal, operation, target, expect?
    eventhubs.json       -- {namespaces:[{id,name,tier,units,public_network,
                            kafka_enabled}], eventhubs:[{id,namespace_id,name,
                            partition_count,retention_hours,consumer_groups,
                            capture}], authorization:[{principal,role,scope}],
                            metrics:{<resource>:{<metric>:[{t,v}]}},
                            events:[{type,at,message}]}
    offsets.json         -- {source:{<hub>:{<partition>:{latest_offset,
                            latest_sequence,enqueue_time}}}}
    consumer.json        -- {consumer_groups:[{name,eventhub_id,owners:[app],
                            checkpoints:{<partition>:{offset,sequence,
                            updated_at}}}]}
    query_progress.json  -- {progress:[StreamingQueryProgress-like dicts]}
    checkpoint.json      -- {location,exists,advancing,age_hours,
                            last_batch_id,owner_query_id,
                            offsets:{<partition>:seq}}
    spark_streaming.json -- {query:{id,run_id,name,status},
                            config:{checkpointLocation,startingOffsets,
                            failOnDataLoss,maxOffsetsPerTrigger,outputMode,
                            trigger,watermark},sink:{type,idempotent,
                            transactional,merge_keys}}
    schema.json          -- {producer:{version,fields},consumer:{...},
                            compatibility,registry}
    eventstream.json     -- {id,workspace_id,name,publish_state,sources:[],
                            transforms:[],destinations:[]}
    eventhouse.json      -- {id,databases:[{name,tables:[{name,
                            last_ingestion_at,row_count}]}],ingestion:{...}}
    activator.json       -- {id,rules:[{id,source_type,source_ref,mapping,
                            condition,evaluation_mode,last_evaluated_at,
                            last_action:{kind,at,status}}]}
    connections.json     -- {id:{auth_kind,target,status}}
    environment.json     -- scope facts (tenant/subscription/region...)
    sample_events.json   -- untrusted payload samples (DATA_ONLY, never
                            drive verdicts)
    notebooks/           -- optional .py/.sql/.ipynb scanned by notebook_scan

Everything is data.  Secrets in connection/SAS payloads are dropped at the
extraction boundary (``collectors.redact``).
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
    "eventhubs", "offsets", "consumer", "query_progress", "checkpoint",
    "spark_streaming", "schema", "eventstream", "eventhouse", "activator",
    "connections", "environment", "sample_events",
)
_SUFFIXES = (".json", ".yaml", ".yml")
NOTEBOOK_SUFFIXES = frozenset({".py", ".sql", ".ipynb"})

#: Layer -> bundle artifact that feeds it (evidence-path + unresolved maps).
LAYER_SOURCE = {
    "event_hubs_auth": "eventhubs",
    "event_hubs_network": "eventhubs",
    "event_hubs_capacity": "eventhubs",
    "partitioning": "offsets",
    "consumer_group": "consumer",
    "consumer_progress": "consumer",
    "checkpoint": "checkpoint",
    "state_store": "query_progress",
    "schema": "schema",
    "spark_processing": "query_progress",
    "sink": "spark_streaming",
    "eventstream_source": "eventstream",
    "eventstream_publish": "eventstream",
    "eventstream_transform": "eventstream",
    "eventstream_destination": "eventstream",
    "eventhouse_ingestion": "eventhouse",
    "kql": "eventhouse",
    "activator_mapping": "activator",
    "activator_evaluation": "activator",
    "cross_environment": "environment",
}


class StreamCaseError(ValueError):
    """Bundle inválido ou ilegível. Surfaces traduzem para exit 2 / erro MCP."""


@dataclass
class StreamBundle:
    """Loaded bundle: case dict, artifact payloads, and the file each came from."""

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
        raise StreamCaseError(f"artifact unreadable: {path.name}") from exc
    try:
        if path.suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except ValueError as exc:
        raise StreamCaseError(
            f"artifact is not valid {path.suffix}: {path.name}") from exc


def load_bundle(root: str | Path) -> StreamBundle:
    root = Path(root)
    if not root.is_dir():
        raise StreamCaseError(f"bundle directory not found: {root}")
    case_file = next((root / f"case{s}" for s in _SUFFIXES
                      if (root / f"case{s}").is_file()), None)
    if case_file is None:
        raise StreamCaseError(f"bundle missing case.yaml: {root}")
    case = _load_payload(case_file)
    if not isinstance(case, Mapping):
        raise StreamCaseError("case.yaml must be a mapping")
    for key in ("principal", "operation", "target"):
        if key not in case:
            raise StreamCaseError(f"case.yaml missing required key: {key}")
    bundle = StreamBundle(root=root, case=dict(case),
                          sources={"case": case_file.name})
    for name in ARTIFACT_NAMES:
        path = next((root / f"{name}{s}" for s in _SUFFIXES
                     if (root / f"{name}{s}").is_file()), None)
        if path is None:
            continue
        payload = _load_payload(path)
        if not isinstance(payload, Mapping):
            raise StreamCaseError(f"{path.name} must be a mapping")
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
    "ARTIFACT_NAMES", "LAYER_SOURCE", "StreamBundle", "StreamCaseError",
    "load_bundle",
]
