"""Streaming correctness semantics (SDD STREAMING_CORRECTNESS).

Delivery is end-to-end — never the name of a framework.  The classifier
only returns what evidence supports:

    at_most_once_possible      checkpoint missing/deleted + start=latest
                               (or non-replayable source)
    at_least_once              replayable source + checkpoint + retryable
                               pipeline; sink not idempotent => duplicate risk
    effectively_once           at-least-once + idempotent/transactional sink
                               (merge keys, dedup key, batch idempotency)
    exactly_once_claim_supported
                               effectively_once + transactional sink and no
                               async progress tracking (Spark docs: async
                               checkpointing breaks exactly-once)
    unresolved                 missing evidence
"""
from __future__ import annotations

from typing import Any

DELIVERY_ORDER = ("unresolved", "at_most_once_possible", "at_least_once",
                  "effectively_once", "exactly_once_claim_supported")


def _attr(items: list[Any], key: str) -> Any:
    for f in items:
        if key in f.attrs:
            return f.attrs[key]
    return None


def _cfg(facts: list[Any], key: str) -> Any:
    for f in facts:
        if f.kind == "stream.config" and f.subject.get("key") == key:
            return f.attrs.get("value")
    return None


def classify_delivery(facts: list[Any]) -> dict[str, Any]:
    """End-to-end delivery classification + evidence it rests on."""
    ev = [f.id for f in facts if f.kind in {
        "stream.checkpoint", "stream.sink", "stream.config",
        "stream.query_meta", "eh.hub", "schema.compat"}]
    checkpoint = [f for f in facts if f.kind == "stream.checkpoint"]
    sink = [f for f in facts if f.kind == "stream.sink"]
    replayable_source = bool([f for f in facts
                              if f.kind in {"eh.hub", "offset.position"}])
    exists = _attr(checkpoint, "exists") if checkpoint else None
    start = _cfg(facts, "startingOffsets") or _cfg(facts, "startingoffsets")
    async_progress = _attr(
        [f for f in facts if f.kind == "stream.query_meta"],
        "async_progress")
    if not checkpoint and not sink:
        return {"classification": "unresolved",
                "reason": "no checkpoint or sink evidence", "evidence": ev}
    if checkpoint and exists is False and str(start).lower() == "latest":
        return {"classification": "at_most_once_possible",
                "reason": "checkpoint deleted + startingOffsets=latest",
                "evidence": ev}
    if not replayable_source and not sink:
        return {"classification": "unresolved",
                "reason": "source replayability unknown", "evidence": ev}
    idempotent = any(f.attrs.get("idempotent") or f.attrs.get("merge_keys")
                     or f.attrs.get("dedup_key") for f in sink)
    transactional = any(f.attrs.get("transactional") for f in sink)
    if checkpoint:
        if transactional and idempotent and async_progress is not True:
            return {"classification": "exactly_once_claim_supported",
                    "reason": "replayable source + checkpoint + "
                              "transactional idempotent sink, synchronous "
                              "progress tracking",
                    "evidence": ev}
        if idempotent or transactional:
            return {"classification": "effectively_once",
                    "reason": "at-least-once pipeline with idempotent or "
                              "transactional sink"
                              + (" (async progress tracking observed — "
                                 "exactly-once not claimable)"
                                 if async_progress is True else ""),
                    "evidence": ev}
        return {"classification": "at_least_once",
                "reason": "checkpointed replayable pipeline; sink not proven "
                          "idempotent — duplicate risk on retry/replay",
                "evidence": ev}
    return {"classification": "unresolved",
            "reason": "checkpoint evidence absent", "evidence": ev}


def schema_compatibility(facts: list[Any]) -> dict[str, Any]:
    """Additive nullable change != breaking type change."""
    compat = [f for f in facts if f.kind == "schema.compat"]
    if compat:
        verdict = str(compat[0].attrs.get("verdict", "unknown"))
        return {"verdict": verdict if verdict in
                {"compatible", "breaking", "unknown"} else "unknown",
                "changes": compat[0].attrs.get("changes"),
                "evidence": [compat[0].id]}
    versions = {f.subject.get("side"): f for f in facts
                if f.kind == "schema.version"}
    prod, cons = versions.get("producer"), versions.get("consumer")
    if prod is None or cons is None:
        return {"verdict": "unknown", "evidence": []}
    pf = {f_["name"]: f_ for f_ in prod.attrs.get("fields") or []}
    cf = {f_["name"]: f_ for f_ in cons.attrs.get("fields") or []}
    breaking = []
    for name, pfield in pf.items():
        cfield = cf.get(name)
        if cfield is None and not pfield.get("nullable", True):
            breaking.append(f"required field '{name}' missing in consumer")
        elif cfield is not None and cfield.get("type") != pfield.get("type"):
            breaking.append(f"type change '{name}': "
                            f"{pfield.get('type')} -> {cfield.get('type')}")
    ev = [f.id for f in (prod, cons)]
    return {"verdict": "breaking" if breaking else "compatible",
            "changes": breaking or None, "evidence": ev}


def data_loss_candidates(facts: list[Any]) -> list[dict[str, Any]]:
    """Retention/positions/checkpoint evidence that supports a *risk* of
    data loss — never confirmed loss unless positions prove it."""
    out: list[dict[str, Any]] = []
    exists = _attr([f for f in facts if f.kind == "stream.checkpoint"],
                   "exists")
    start = _cfg(facts, "startingOffsets") or _cfg(facts, "startingoffsets")
    ck_ev = [f.id for f in facts if f.kind == "stream.checkpoint"]
    if exists is False and str(start).lower() == "latest":
        out.append({
            "kind": "checkpoint_deleted_start_latest",
            "severity": "high",
            "evidence": ck_ev,
            "explanation": "checkpoint ausente + startingOffsets=latest: "
                           "replay de posições antigas é impossível — "
                           "RISCO de perda, não perda confirmada.",
        })
    retention = None
    for f in facts:
        if f.kind == "eh.hub" and f.attrs.get("retention_hours"):
            retention = f.attrs["retention_hours"]
    cp_age = _attr([f for f in facts if f.kind == "stream.checkpoint"],
                   "age_hours")
    if retention and isinstance(cp_age, (int, float)) and cp_age > retention:
        out.append({
            "kind": "checkpoint_older_than_retention",
            "severity": "high",
            "evidence": ck_ev,
            "explanation": f"checkpoint tem {cp_age}h e retention do hub é "
                           f"{retention}h — posições do checkpoint já saíram "
                           "da janela de retenção; replay impossível para o "
                           "trecho expirado.",
        })
    return out


__all__ = ["DELIVERY_ORDER", "classify_delivery", "data_loss_candidates",
           "schema_compatibility"]
