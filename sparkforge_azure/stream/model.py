"""Streaming domain model — Event Hubs + Structured Streaming + Fabric RTI
(SDDs EVENT_HUBS_DEEP / STRUCTURED_STREAMING / STREAMING_CORRECTNESS /
FABRIC_RTI).

Streaming is temporal and stateful: a partition is an ordered log, a
consumer group is an independent view, a checkpoint is operational state —
not a directory.  Lag needs two positions (source vs consumer); a single
metric point is never a trend.

Fact kinds are versioned by contract.  Official IDs (ARM id / REST GUID) are
identity; display names are attributes, never subject keys.
"""
from __future__ import annotations

#: Public failure-layer vocabulary for the streaming vertical (prompt #225-226):
#: each layer is a distinct diagnosable cause with its own evidence.
STREAM_LAYERS = (
    "event_hubs_auth",
    "event_hubs_network",
    "event_hubs_capacity",
    "partitioning",
    "consumer_group",
    "consumer_progress",
    "checkpoint",
    "state_store",
    "schema",
    "spark_processing",
    "sink",
    "eventstream_source",
    "eventstream_publish",
    "eventstream_transform",
    "eventstream_destination",
    "eventhouse_ingestion",
    "kql",
    "activator_mapping",
    "activator_evaluation",
    "cross_environment",
    "unresolved",
)

#: Layers belonging to the Event Hubs / Structured Streaming side
#: (Databricks or any Spark host) vs the Fabric RTI side.
EH_SIDE_LAYERS = frozenset(STREAM_LAYERS[:11])
RTI_SIDE_LAYERS = frozenset({
    "eventstream_source", "eventstream_publish", "eventstream_transform",
    "eventstream_destination", "eventhouse_ingestion", "kql",
    "activator_mapping", "activator_evaluation",
})

#: Delivery-semantics vocabulary (prompt #54) — closed set; never claimed
#: beyond evidence.  ``exactly_once_claim_supported`` requires the full
#: chain (source replayable + checkpoint + deterministic transform +
#: idempotent/transactional sink).
DELIVERY_CLASSES = frozenset({
    "at_most_once_possible",
    "at_least_once",
    "effectively_once",
    "exactly_once_claim_supported",
    "unresolved",
})

#: Event Hubs authorization modes observed in bundles.
EH_AUTH_MODES = frozenset({"rbac", "sas", "connection_string", "unknown"})

#: Eventstream publish states (current Fabric RTI docs).
EVENTSTREAM_PUBLISH_STATES = frozenset({"published", "draft", "unknown"})

#: Activator rule source types.
ACTIVATOR_SOURCE_TYPES = frozenset({"eventstream", "kql_queryset", "unknown"})

#: Streaming health is multi-axis (prompt #26) — no magic boolean.
HEALTH_AXES = (
    "source_availability", "partition_health", "consumer_progress",
    "checkpoint_freshness", "processing_latency", "sink_progress",
    "schema_health", "state_health",
)


def eventhub_id(hub_id: str | None, namespace_id: str | None,
                name: str | None) -> str:
    """Deterministic Event Hub identity: official/ARM id when present."""
    if hub_id:
        return str(hub_id)
    if namespace_id and name:
        return f"{namespace_id}/{name}"
    return f"{namespace_id or 'namespace-unknown'}:{name or 'hub-unknown'}"
