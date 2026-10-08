"""Deterministic extractors: streaming artifacts -> Facts (SDD EVENT_HUBS_DEEP).

Same contract as ``fabric.extract``: no judgement — Facts are anchored
observations.  Metrics stay time-series (a single point is never a trend);
positions are modeled per partition (source vs consumer separately).
Secrets never reach Facts — ``collectors.redact`` strips them at the
boundary.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sparkforge_azure.findings.models import Fact, sort_facts
from sparkforge_azure.stream.model import eventhub_id

Prov = dict[str, Any]

_ENV_KEYS = ("tenant_id", "subscription_id", "workspace_id", "namespace_id",
             "region", "cloud")


def _p(prov: Prov, extractor: str) -> Prov:
    return {**prov, "extractor": extractor}


def _num(v: Any) -> int | float | None:
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def extract_eventhubs(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_eventhubs")
    facts: list[Fact] = []
    ns_by_id: dict[str, Mapping[str, Any]] = {}
    for ns in payload.get("namespaces") or []:
        if isinstance(ns, Mapping) and ns.get("id"):
            ns_by_id[str(ns["id"])] = ns
            facts.append(Fact(
                kind="eh.namespace",
                subject={"namespace_id": str(ns["id"])},
                attrs={k: v for k, v in {
                    "name": ns.get("name"), "tier": ns.get("tier"),
                    "throughput_units": _num(ns.get("throughput_units")),
                    "processing_units": _num(ns.get("processing_units")),
                    "capacity_units": _num(ns.get("capacity_units")),
                    "public_network": ns.get("public_network"),
                    "kafka_enabled": ns.get("kafka_enabled"),
                    "private_endpoints": ns.get("private_endpoints"),
                }.items() if v is not None},
                provenance=dict(prov)))
    for hub in payload.get("eventhubs") or []:
        if not isinstance(hub, Mapping):
            continue
        hid = eventhub_id(hub.get("id"), hub.get("namespace_id"),
                          hub.get("name"))
        nsp = str(hub.get("namespace_id", ""))
        facts.append(Fact(
            kind="eh.hub",
            subject={"hub_id": hid, "namespace_id": nsp},
            attrs={k: v for k, v in {
                "name": hub.get("name"),
                "partition_count": _num(hub.get("partition_count")),
                "retention_hours": _num(hub.get("retention_hours")),
                "capture": hub.get("capture"),
            }.items() if v is not None},
            provenance=dict(prov)))
        for pid in hub.get("partitions") or range(
                int(hub.get("partition_count") or 0)):
            facts.append(Fact(kind="eh.partition",
                              subject={"hub_id": hid,
                                       "partition": str(pid)},
                              attrs={}, provenance=dict(prov)))
        for cg in hub.get("consumer_groups") or []:
            name = cg.get("name") if isinstance(cg, Mapping) else cg
            if not name:
                continue
            facts.append(Fact(kind="eh.consumer_group",
                              subject={"hub_id": hid, "name": str(name)},
                              attrs={}, provenance=dict(prov)))
    for az in payload.get("authorization") or []:
        if not isinstance(az, Mapping):
            continue
        facts.append(Fact(
            kind="eh.authz",
            subject={"principal": str(az.get("principal", "")),
                     "scope": str(az.get("scope", ""))},
            attrs={k: v for k, v in {
                "role": az.get("role"), "effect": az.get("effect"),
                "auth_mode": az.get("auth_mode"),
            }.items() if v is not None},
            provenance=dict(prov)))
    metrics = payload.get("metrics") or {}
    if isinstance(metrics, Mapping):
        for resource, series in sorted(metrics.items()):
            if not isinstance(series, Mapping):
                continue
            for metric, points in sorted(series.items()):
                pts = [pt for pt in (points or []) if isinstance(pt, Mapping)]
                facts.append(Fact(
                    kind="eh.metric",
                    subject={"resource": str(resource),
                             "metric": str(metric)},
                    attrs={"points": pts, "points_count": len(pts),
                           "latest": pts[-1] if pts else None},
                    provenance=dict(prov)))
                if str(metric) in {"throttled_requests", "server_busy",
                                   "incoming_rejected"}:
                    total = sum(_num(pt.get("v")) or 0 for pt in pts)
                    if total > 0:
                        facts.append(Fact(
                            kind="eh.throttle",
                            subject={"resource": str(resource),
                                     "signal": str(metric)},
                            attrs={"total": total,
                                   "points": len(pts)},
                            provenance=dict(prov)))
    for ev in payload.get("events") or []:
        if isinstance(ev, Mapping):
            facts.append(Fact(
                kind="eh.event",
                subject={"resource": str(ev.get("resource", "namespace")),
                         "type": str(ev.get("type", "unknown"))},
                attrs={k: v for k, v in ev.items()
                       if isinstance(v, (str, int, float, bool))},
                provenance=dict(prov)))
    return sort_facts(facts)


def extract_offsets(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """Source-side positions: latest offset/sequence per partition."""
    prov = _p(prov, "extract_offsets")
    facts: list[Fact] = []
    source = payload.get("source") or {}
    for hub_id, parts in sorted(source.items()):
        if not isinstance(parts, Mapping):
            continue
        for part, pos in sorted(parts.items()):
            if not isinstance(pos, Mapping):
                continue
            facts.append(Fact(
                kind="offset.position",
                subject={"hub_id": str(hub_id), "partition": str(part)},
                attrs={k: v for k, v in {
                    "latest_offset": _num(pos.get("latest_offset")),
                    "latest_sequence": _num(pos.get("latest_sequence")),
                    "enqueue_time": pos.get("enqueue_time"),
                    "observed_at": pos.get("observed_at"),
                }.items() if v is not None},
                provenance=dict(prov)))
    return sort_facts(facts)


def extract_consumer(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """Consumer-side progress: group ownership + per-partition checkpoints."""
    prov = _p(prov, "extract_consumer")
    facts: list[Fact] = []
    for cg in payload.get("consumer_groups") or []:
        if not isinstance(cg, Mapping):
            continue
        name = str(cg.get("name", ""))
        hub = str(cg.get("eventhub_id", ""))
        owners = sorted(str(o) for o in cg.get("owners") or [])
        facts.append(Fact(
            kind="consumer.group",
            subject={"hub_id": hub, "name": name},
            attrs={"owners": owners, "owner_count": len(owners),
                   "apps": sorted(str(a) for a in cg.get("apps") or [])},
            provenance=dict(prov)))
        for owner in owners:
            facts.append(Fact(
                kind="consumer.owner",
                subject={"hub_id": hub, "consumer_group": name,
                         "owner": owner},
                attrs={}, provenance=dict(prov)))
        cps = cg.get("checkpoints") or {}
        if isinstance(cps, Mapping):
            for part, cp in sorted(cps.items()):
                if not isinstance(cp, Mapping):
                    continue
                facts.append(Fact(
                    kind="consumer.checkpoint",
                    subject={"hub_id": hub, "consumer_group": name,
                             "partition": str(part)},
                    attrs={k: v for k, v in {
                        "offset": _num(cp.get("offset")),
                        "sequence": _num(cp.get("sequence")),
                        "updated_at": cp.get("updated_at"),
                    }.items() if v is not None},
                    provenance=dict(prov)))
    return sort_facts(facts)


def extract_query_progress(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """StreamingQueryProgress events -> stream.query + stream.progress facts."""
    prov = _p(prov, "extract_query_progress")
    facts: list[Fact] = []
    for ev in payload.get("progress") or []:
        if not isinstance(ev, Mapping):
            continue
        qid = str(ev.get("id") or ev.get("query_id") or "")
        run = str(ev.get("runId") or ev.get("run_id") or "")
        if not facts or all(
                not (f.kind == "stream.query"
                     and f.subject.get("query_id") == qid)
                for f in facts):
            facts.append(Fact(
                kind="stream.query",
                subject={"query_id": qid or "unknown"},
                attrs={"run_id": run, "name": ev.get("name"),
                       "status": ev.get("status")},
                provenance=dict(prov)))
        batch = _num(ev.get("batchId") if "batchId" in ev
                     else ev.get("batch_id"))
        dur = ev.get("durationMs") or ev.get("duration_ms") or {}
        state_ops = ev.get("stateOperators") or ev.get("state_operators") or []
        state_rows = None
        for op in state_ops:
            if isinstance(op, Mapping):
                rows = _num(op.get("numRowsTotal"))
                if rows is not None:
                    state_rows = (state_rows or 0) + rows
        facts.append(Fact(
            kind="stream.progress",
            subject={"query_id": qid or "unknown",
                     "batch_id": str(int(batch) if batch is not None else "?")},
            attrs={k: v for k, v in {
                "timestamp": ev.get("timestamp"),
                "input_rate": _num(ev.get("inputRowsPerSecond")
                                   or ev.get("input_rate")),
                "process_rate": _num(ev.get("processedRowsPerSecond")
                                     or ev.get("process_rate")),
                "num_input": _num(ev.get("numInputRows")
                                  or ev.get("num_input")),
                "batch_duration_ms": _num(dur.get("addBatch")
                                          if isinstance(dur, Mapping)
                                          else dur),
                "trigger_ms": _num(ev.get("triggerExecutionMs")),
                "watermark": (ev.get("eventTime") or {}).get("watermark")
                if isinstance(ev.get("eventTime"), Mapping) else None,
                "state_rows_total": state_rows,
                "start_offsets": ev.get("start_offsets"),
                "end_offsets": ev.get("end_offsets"),
            }.items() if v is not None},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_checkpoint(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_checkpoint")
    facts: list[Fact] = []
    loc = str(payload.get("location", ""))
    attrs = {k: v for k, v in {
        "exists": payload.get("exists"),
        "advancing": payload.get("advancing"),
        "age_hours": _num(payload.get("age_hours")),
        "last_batch_id": _num(payload.get("last_batch_id")),
        "owner_query_id": payload.get("owner_query_id"),
        "format_compatible": payload.get("format_compatible"),
        "commits": _num(payload.get("commits")),
    }.items() if v is not None}
    facts.append(Fact(kind="stream.checkpoint",
                      subject={"location": loc or "unknown"},
                      attrs=attrs, provenance=dict(prov)))
    offsets = payload.get("offsets") or {}
    if isinstance(offsets, Mapping):
        for part, seq in sorted(offsets.items()):
            facts.append(Fact(
                kind="stream.checkpoint_offset",
                subject={"location": loc or "unknown",
                         "partition": str(part)},
                attrs={"sequence": _num(seq)}, provenance=dict(prov)))
    return sort_facts(facts)


def extract_spark_streaming(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_spark_streaming")
    facts: list[Fact] = []
    query = payload.get("query") or {}
    if isinstance(query, Mapping) and query.get("id"):
        facts.append(Fact(
            kind="stream.query_meta",
            subject={"query_id": str(query["id"])},
            attrs={k: v for k, v in {
                "run_id": query.get("run_id"), "name": query.get("name"),
                "status": query.get("status"),
                "async_progress": query.get("async_progress"),
            }.items() if v is not None},
            provenance=dict(prov)))
    config = payload.get("config") or {}
    if isinstance(config, Mapping):
        for key, value in sorted(config.items()):
            if isinstance(value, (str, int, float, bool)) or value is None:
                facts.append(Fact(
                    kind="stream.config",
                    subject={"key": str(key)},
                    attrs={"value": value}, provenance=dict(prov)))
    sink = payload.get("sink") or {}
    if isinstance(sink, Mapping) and sink:
        stype = str(sink.get("type", "unknown"))
        facts.append(Fact(
            kind="stream.sink",
            subject={"sink": str(sink.get("id", stype))},
            attrs={k: v for k, v in {
                "type": stype,
                "idempotent": sink.get("idempotent"),
                "transactional": sink.get("transactional"),
                "merge_keys": sink.get("merge_keys"),
                "dedup_key": sink.get("dedup_key"),
                "status": sink.get("status"),
                "last_write_at": sink.get("last_write_at"),
                "error": sink.get("error"),
            }.items() if v is not None},
            provenance=dict(prov)))
    return sort_facts(facts)


def _field_sig(fields: Any) -> list[dict[str, Any]]:
    out = []
    for f in fields or []:
        if isinstance(f, Mapping):
            out.append({"name": str(f.get("name", "")),
                        "type": str(f.get("type", "")),
                        "nullable": bool(f.get("nullable", True))})
    return out


def extract_schema(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_schema")
    facts: list[Fact] = []
    for side in ("producer", "consumer"):
        schema = payload.get(side)
        if not isinstance(schema, Mapping):
            continue
        facts.append(Fact(
            kind="schema.version",
            subject={"side": side,
                     "version": str(schema.get("version", "unknown"))},
            attrs={"fields": _field_sig(schema.get("fields")),
                   "source": schema.get("source")},
            provenance=dict(prov)))
    compat = payload.get("compatibility")
    if isinstance(compat, Mapping):
        facts.append(Fact(
            kind="schema.compat",
            subject={"registry": str(payload.get("registry", "inline"))},
            attrs={"verdict": str(compat.get("verdict", "unknown")),
                   "changes": compat.get("changes"),
                   "mode": compat.get("mode")},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_eventstream(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_eventstream")
    facts: list[Fact] = []
    esid = str(payload.get("id", ""))
    if not esid:
        return facts
    facts.append(Fact(
        kind="rti.eventstream",
        subject={"eventstream_id": esid,
                 "workspace_id": str(payload.get("workspace_id", ""))},
        attrs={k: v for k, v in {
            "name": payload.get("name"),
            "publish_state": payload.get("publish_state"),
            "schema_aware": payload.get("schema_aware"),
            "preview": payload.get("preview"),
        }.items() if v is not None},
        provenance=dict(prov)))
    for src in payload.get("sources") or []:
        if not isinstance(src, Mapping):
            continue
        facts.append(Fact(
            kind="rti.es_source",
            subject={"eventstream_id": esid,
                     "source_id": str(src.get("id", src.get("type", "?")))},
            attrs={k: v for k, v in {
                "type": src.get("type"),
                "connection_id": src.get("connection_id"),
                "status": src.get("status"),
                "error": src.get("error"),
            }.items() if v is not None},
            provenance=dict(prov)))
    for tr in payload.get("transforms") or []:
        if not isinstance(tr, Mapping):
            continue
        facts.append(Fact(
            kind="rti.es_transform",
            subject={"eventstream_id": esid,
                     "transform_id": str(tr.get("id", tr.get("kind", "?")))},
            attrs={k: v for k, v in {
                "kind": tr.get("kind"), "status": tr.get("status"),
                "error": tr.get("error"),
            }.items() if v is not None},
            provenance=dict(prov)))
    for dst in payload.get("destinations") or []:
        if not isinstance(dst, Mapping):
            continue
        facts.append(Fact(
            kind="rti.es_destination",
            subject={"eventstream_id": esid,
                     "destination_id": str(dst.get("id",
                                                  dst.get("type", "?")))},
            attrs={k: v for k, v in {
                "type": dst.get("type"), "target_id": dst.get("target_id"),
                "status": dst.get("status"), "error": dst.get("error"),
                "ingestion_mode": dst.get("ingestion_mode"),
            }.items() if v is not None},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_eventhouse(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_eventhouse")
    facts: list[Fact] = []
    eid = str(payload.get("id", ""))
    if not eid:
        return facts
    facts.append(Fact(kind="rti.eventhouse",
                      subject={"eventhouse_id": eid},
                      attrs={"name": payload.get("name")},
                      provenance=dict(prov)))
    for db in payload.get("databases") or []:
        if not isinstance(db, Mapping):
            continue
        dbn = str(db.get("name", ""))
        for tbl in db.get("tables") or []:
            if not isinstance(tbl, Mapping):
                continue
            facts.append(Fact(
                kind="rti.ingestion",
                subject={"eventhouse_id": eid, "database": dbn,
                         "table": str(tbl.get("name", ""))},
                attrs={k: v for k, v in {
                    "last_ingestion_at": tbl.get("last_ingestion_at"),
                    "row_count": _num(tbl.get("row_count")),
                    "ingestion_lag_ms": _num(tbl.get("ingestion_lag_ms")),
                    "errors": tbl.get("errors"),
                }.items() if v is not None},
                provenance=dict(prov)))
    ing = payload.get("ingestion")
    if isinstance(ing, Mapping):
        facts.append(Fact(
            kind="rti.ingestion_status",
            subject={"eventhouse_id": eid},
            attrs={k: v for k, v in {
                "status": ing.get("status"),
                "lag_ms": _num(ing.get("lag_ms")),
                "errors": ing.get("errors"),
            }.items() if v is not None},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_activator(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_activator")
    facts: list[Fact] = []
    aid = str(payload.get("id", ""))
    if not aid:
        return facts
    facts.append(Fact(kind="rti.activator",
                      subject={"activator_id": aid},
                      attrs={"name": payload.get("name")},
                      provenance=dict(prov)))
    for rule in payload.get("rules") or []:
        if not isinstance(rule, Mapping):
            continue
        rid = str(rule.get("id", ""))
        last_action = rule.get("last_action") or {}
        facts.append(Fact(
            kind="rti.activator_rule",
            subject={"activator_id": aid, "rule_id": rid},
            attrs={k: v for k, v in {
                "source_type": rule.get("source_type"),
                "source_ref": rule.get("source_ref"),
                "mapping_valid": rule.get("mapping_valid"),
                "condition": rule.get("condition"),
                "evaluation_mode": rule.get("evaluation_mode"),
                "last_evaluated_at": rule.get("last_evaluated_at"),
                "query_stale": rule.get("query_stale"),
                "action_kind": last_action.get("kind")
                if isinstance(last_action, Mapping) else None,
                "action_status": last_action.get("status")
                if isinstance(last_action, Mapping) else None,
                "action_at": last_action.get("at")
                if isinstance(last_action, Mapping) else None,
            }.items() if v is not None},
            provenance=dict(prov)))
    return sort_facts(facts)


def extract_connections(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    prov = _p(prov, "extract_connections")
    facts: list[Fact] = []
    for cid, conn in sorted(payload.items()):
        if not isinstance(conn, Mapping):
            continue
        facts.append(Fact(
            kind="stream.connection",
            subject={"connection_id": str(cid)},
            attrs={k: v for k, v in {
                "auth_kind": conn.get("auth_kind"),
                "target": conn.get("target"),
                "status": conn.get("status"),
                "error": conn.get("error"),
            }.items() if v is not None},
            provenance=dict(prov)))
    return sort_facts(facts)


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
        if not isinstance(payload, Mapping) or name == "sample_events":
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


def extract_sample_events(payload: Mapping[str, Any], prov: Prov) -> list[Fact]:
    """Sample event payloads: presence-only facts.  Payload content is
    DATA_ONLY — we record count/size/hash hints, never bodies."""
    prov = _p(prov, "extract_sample_events")
    events = payload.get("events") or []
    facts = [Fact(
        kind="stream.sample_events",
        subject={"artifact": "sample_events"},
        attrs={"count": len(events)},
        provenance=dict(prov))]
    return sort_facts(facts)


_EXTRACTORS = {
    "eventhubs": extract_eventhubs,
    "offsets": extract_offsets,
    "consumer": extract_consumer,
    "query_progress": extract_query_progress,
    "checkpoint": extract_checkpoint,
    "spark_streaming": extract_spark_streaming,
    "schema": extract_schema,
    "eventstream": extract_eventstream,
    "eventhouse": extract_eventhouse,
    "activator": extract_activator,
    "connections": extract_connections,
    "sample_events": extract_sample_events,
}


def extract_all(artifacts: Mapping[str, Any],
                sources: Mapping[str, str]) -> list[Fact]:
    """Run every extractor whose artifact is present.

    Artifacts are redacted at the extraction boundary: bundle files stay
    byte-identical on disk, but Facts never carry secret material.
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
    "extract_activator", "extract_all", "extract_checkpoint",
    "extract_connections", "extract_consumer", "extract_env",
    "extract_eventhouse", "extract_eventhubs", "extract_eventstream",
    "extract_offsets", "extract_query_progress", "extract_sample_events",
    "extract_schema", "extract_spark_streaming",
]
