"""Fabric Real-Time Intelligence sub-chain (SDD FABRIC_RTI).

Eventstream != Eventhouse != Activator — each has its own responsibility and
failure semantics:

    source (connection/auth) -> publish state -> transforms -> destinations
      -> eventhouse ingestion -> kql queryset -> activator mapping
      -> activator evaluation -> action evidence

``rule evaluated`` never means ``business action succeeded``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RTIStage:
    layer: str
    verdict: str            # pass | fail | unknown | not_evaluated
    reason: str
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"layer": self.layer, "verdict": self.verdict,
                "reason": self.reason, "evidence": self.evidence}


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _bad(items: list[Any]) -> list[Any]:
    return [i for i in items
            if str(i.attrs.get("status", "")).lower()
            in {"error", "failed", "unauthorized", "denied", "broken"}
            or i.attrs.get("error")]


def evaluate_rti(facts: list[Any]) -> list[RTIStage]:
    """Evaluate the RTI chain; returns stages in order (empty when no RTI
    artifacts were extracted)."""
    stages: list[RTIStage] = []
    streams = _facts(facts, "rti.eventstream")
    sources = _facts(facts, "rti.es_source")
    transforms = _facts(facts, "rti.es_transform")
    destinations = _facts(facts, "rti.es_destination")
    houses = _facts(facts, "rti.eventhouse")
    ingestions = [*_facts(facts, "rti.ingestion"),
                  *_facts(facts, "rti.ingestion_status")]
    activators = _facts(facts, "rti.activator")
    rules = _facts(facts, "rti.activator_rule")
    if not (streams or houses or activators):
        return stages

    # --- eventstream_source -------------------------------------------
    if not sources:
        stages.append(RTIStage("eventstream_source", "unknown",
                               "no source facts observed", []))
    else:
        bad = _bad(sources)
        if bad:
            stages.append(RTIStage(
                "eventstream_source", "fail",
                "source error: " + "; ".join(
                    f"{s.subject.get('source_id')}="
                    f"{s.attrs.get('error') or s.attrs.get('status')}"
                    for s in bad),
                [s.id for s in bad]))
        else:
            stages.append(RTIStage("eventstream_source", "pass",
                                   f"{len(sources)} source(s) healthy",
                                   [s.id for s in sources]))

    # --- eventstream_publish ------------------------------------------
    unpublished = [s for s in streams
                   if str(s.attrs.get("publish_state", "published")).lower()
                   != "published"]
    if unpublished:
        stages.append(RTIStage(
            "eventstream_publish", "fail",
            "eventstream not published: " + "; ".join(
                f"{s.subject.get('eventstream_id')}="
                f"{s.attrs.get('publish_state')}" for s in unpublished),
            [s.id for s in unpublished]))
    elif streams:
        stages.append(RTIStage("eventstream_publish", "pass",
                               "all eventstreams published",
                               [s.id for s in streams]))

    # --- eventstream_transform -----------------------------------------
    bad_tr = _bad(transforms)
    if bad_tr:
        stages.append(RTIStage(
            "eventstream_transform", "fail",
            "transform error: " + "; ".join(
                str(t.attrs.get("error") or t.attrs.get("status"))
                for t in bad_tr),
            [t.id for t in bad_tr]))
    elif transforms:
        stages.append(RTIStage("eventstream_transform", "pass",
                               f"{len(transforms)} transform(s) ok",
                               [t.id for t in transforms]))

    # --- eventstream_destination ---------------------------------------
    if destinations:
        bad_dst = _bad(destinations)
        if bad_dst:
            stages.append(RTIStage(
                "eventstream_destination", "fail",
                "destination error: " + "; ".join(
                    f"{d.subject.get('destination_id')}="
                    f"{d.attrs.get('error') or d.attrs.get('status')}"
                    for d in bad_dst),
                [d.id for d in bad_dst]))
        else:
            stages.append(RTIStage("eventstream_destination", "pass",
                                   f"{len(destinations)} destination(s) ok",
                                   [d.id for d in destinations]))

    # --- eventhouse_ingestion -------------------------------------------
    if ingestions:
        lagged = [i for i in ingestions
                  if (i.attrs.get("ingestion_lag_ms")
                      or i.attrs.get("lag_ms") or 0) > 60_000
                  or i.attrs.get("errors")
                  or str(i.attrs.get("status", "ok")).lower()
                  in {"error", "failed", "degraded"}]
        if lagged:
            stages.append(RTIStage(
                "eventhouse_ingestion", "fail",
                "ingestion degraded: " + "; ".join(
                    f"{i.subject.get('table', i.subject.get('eventhouse_id'))}"
                    for i in lagged),
                [i.id for i in lagged]))
        else:
            stages.append(RTIStage("eventhouse_ingestion", "pass",
                                   f"{len(ingestions)} ingestion target(s) ok",
                                   [i.id for i in ingestions]))

    # --- kql --------------------------------------------------------------
    if houses and not ingestions:
        stages.append(RTIStage("kql", "unknown",
                               "eventhouse present but no table-level "
                               "ingestion facts", []))

    # --- activator_mapping ------------------------------------------------
    invalid = [r for r in rules
               if r.attrs.get("mapping_valid") is False]
    if invalid:
        stages.append(RTIStage(
            "activator_mapping", "fail",
            "rule mapping invalid: " + "; ".join(
                str(r.subject.get("rule_id")) for r in invalid),
            [r.id for r in invalid]))
    elif rules:
        stages.append(RTIStage("activator_mapping", "pass",
                               f"{len(rules)} rule(s) mapped",
                               [r.id for r in rules]))

    # --- activator_evaluation ----------------------------------------------
    stale = [r for r in rules
             if r.attrs.get("query_stale") is True
             or (r.attrs.get("source_type") == "kql_queryset"
                 and not r.attrs.get("last_evaluated_at"))]
    if stale:
        stages.append(RTIStage(
            "activator_evaluation", "fail",
            "rule evaluation stale/unobserved: " + "; ".join(
                str(r.subject.get("rule_id")) for r in stale)
            + " — evaluation semantics, not a streaming source issue",
            [r.id for r in stale]))
    elif rules:
        stages.append(RTIStage("activator_evaluation", "pass",
                               "rules evaluated",
                               [r.id for r in rules]))
    return stages


__all__ = ["RTIStage", "evaluate_rti"]
