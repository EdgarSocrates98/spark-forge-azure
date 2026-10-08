"""Streaming diagnosis — deterministic chain evaluation (Cycle 4).

Two sides, one chain.  The Event Hubs / Structured Streaming side::

    event_hubs_auth → event_hubs_network → event_hubs_capacity
      → partitioning → consumer_group → consumer_progress
      → checkpoint → state_store → schema → spark_processing → sink

The Fabric RTI side (from ``rti.evaluate_rti``)::

    eventstream_source → eventstream_publish → eventstream_transform
      → eventstream_destination → eventhouse_ingestion → kql
      → activator_mapping → activator_evaluation

``UNKNOWN`` never means pass: the failure layer is the first DENY, or
``unresolved`` when evidence cannot complete the chain.  Correctness
semantics (delivery classification, schema compat, data-loss candidates)
become findings, never a pass/fail verdict by themselves.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sparkforge_azure.azure.governance.model import Verdict
from sparkforge_azure.findings.models import Finding
from sparkforge_azure.stream import correctness, progress, rti


@dataclass
class StageVerdict:
    layer: str
    verdict: Verdict
    identity: str
    reason: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"layer": self.layer, "verdict": self.verdict.value,
                "identity": self.identity, "reason": self.reason,
                "evidence": self.evidence}


@dataclass
class StreamDiagnosis:
    status: str                     # allowed | denied | unresolved
    failure_layer: str | None
    chain: list[StageVerdict]
    findings: list[Finding]
    conflicts: list[str]
    scenario: str = ""
    delivery: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "failure_layer": self.failure_layer,
                "chain": [s.to_dict() for s in self.chain],
                "findings": [f.to_dict() for f in self.findings],
                "conflicts": self.conflicts, "scenario": self.scenario,
                "delivery": self.delivery}


def _f(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _mkfinding(rule_id: str, layer: str, title: str, severity: str,
               confidence: str, evidence: list[str], explanation: str,
               changes: list[str], risks: list[str],
               measured: dict[str, Any] | None = None) -> Finding:
    return Finding(
        rule_id=rule_id, title=title, severity=severity,
        confidence=confidence, status="confirmed",
        subject={"case": "", "layer": layer}, evidence=evidence,
        measured=measured or {}, explanation=explanation,
        proposed_change=changes, risks=risks)


# --- EH-side stage evaluators -------------------------------------------


def _stage_auth(facts: list[Any]) -> StageVerdict:
    authz = _f(facts, "eh.authz")
    denied = [a for a in authz
              if str(a.attrs.get("effect", "")).lower() == "deny"
              or str(a.attrs.get("status", "")).lower() == "denied"]
    errors = [e for e in _f(facts, "eh.event")
              if str(e.attrs.get("type", "")).lower()
              in {"auth_failure", "unauthorized", "forbidden", "401", "403"}]
    if denied or errors:
        return StageVerdict(
            "event_hubs_auth", Verdict.DENY, "event_hubs",
            "authorization denied/failed",
            [a.id for a in denied] + [e.id for e in errors])
    if authz:
        return StageVerdict("event_hubs_auth", Verdict.ALLOW, "event_hubs",
                            f"{len(authz)} authorization binding(s) observed",
                            [a.id for a in authz])
    if _f(facts, "eh.namespace"):
        return StageVerdict("event_hubs_auth", Verdict.UNKNOWN, "event_hubs",
                            "namespace observed but no authorization facts")
    return StageVerdict("event_hubs_auth", Verdict.NOT_APPLICABLE,
                        "event_hubs", "no Event Hubs artifacts")


def _stage_network(facts: list[Any]) -> StageVerdict:
    nss = _f(facts, "eh.namespace")
    if not nss:
        return StageVerdict("event_hubs_network", Verdict.NOT_APPLICABLE,
                            "event_hubs", "no namespace facts")
    ev: list[str] = []
    blocked = []
    for ns in nss:
        ev.append(ns.id)
        if ns.attrs.get("public_network") is False and not ns.attrs.get(
                "private_endpoints"):
            blocked.append(ns)
    errors = [e for e in _f(facts, "eh.event")
              if str(e.attrs.get("type", "")).lower()
              in {"network_error", "connection_refused", "timeout"}]
    if blocked or errors:
        return StageVerdict(
            "event_hubs_network", Verdict.DENY, "event_hubs",
            "public network disabled without private endpoint or "
            "connectivity errors observed",
            [b.id for b in blocked] + [e.id for e in errors])
    return StageVerdict("event_hubs_network", Verdict.ALLOW, "event_hubs",
                        "namespace network posture allows traffic", ev)


def _stage_capacity(facts: list[Any]) -> StageVerdict:
    throttles = _f(facts, "eh.throttle")
    if throttles:
        return StageVerdict(
            "event_hubs_capacity", Verdict.DENY, "event_hubs",
            "throttling evidence: " + "; ".join(
                f"{t.subject.get('signal')}={t.attrs.get('total')}"
                for t in throttles),
            [t.id for t in throttles])
    if _f(facts, "eh.namespace") or _f(facts, "eh.metric"):
        return StageVerdict("event_hubs_capacity", Verdict.ALLOW,
                            "event_hubs", "no throttling observed",
                            [f.id for f in _f(facts, "eh.metric")])
    return StageVerdict("event_hubs_capacity", Verdict.NOT_APPLICABLE,
                        "event_hubs", "no namespace/metric facts")


def _stage_partitioning(facts: list[Any]) -> StageVerdict:
    skewed, detail = progress.partition_skew(facts)
    if skewed:
        return StageVerdict(
            "partitioning", Verdict.DENY, "event_hubs",
            f"partition skew x{detail['skew_ratio']}: "
            f"{', '.join(detail['hot_partitions'])}",
            detail["evidence"])
    if _f(facts, "eh.partition") or _f(facts, "offset.position"):
        return StageVerdict("partitioning", Verdict.ALLOW, "event_hubs",
                            "no partition-level skew", [])
    return StageVerdict("partitioning", Verdict.NOT_APPLICABLE,
                        "event_hubs", "no partition/position facts")


def _stage_consumer_group(facts: list[Any]) -> StageVerdict:
    groups = _f(facts, "consumer.group")
    shared = [g for g in groups
              if len(set(g.attrs.get("apps") or [])) > 1]
    if shared:
        return StageVerdict(
            "consumer_group", Verdict.DENY, "consumer",
            "consumer group shared by multiple apps: " + "; ".join(
                f"{g.subject.get('name')}<-{g.attrs.get('apps')}"
                for g in shared),
            [g.id for g in shared])
    if groups or _f(facts, "eh.consumer_group"):
        return StageVerdict("consumer_group", Verdict.ALLOW, "consumer",
                            "consumer groups unambiguous",
                            [g.id for g in groups])
    if _f(facts, "offset.position"):
        return StageVerdict("consumer_group", Verdict.UNKNOWN, "consumer",
                            "source positions exist but no consumer-group "
                            "facts")
    return StageVerdict("consumer_group", Verdict.NOT_APPLICABLE,
                        "consumer", "no consumer artifacts")


def _stage_consumer_progress(facts: list[Any]) -> StageVerdict:
    stalled, ev = progress.consumer_stalled(facts)
    if stalled:
        return StageVerdict("consumer_progress", Verdict.DENY, "consumer",
                            "source advancing while consumer checkpoints "
                            "stand still (stalled)", ev)
    cps = _f(facts, "consumer.checkpoint")
    if cps:
        # caught up is only claimable within the observed window.
        return StageVerdict("consumer_progress", Verdict.ALLOW, "consumer",
                            f"{len(cps)} checkpoint(s) tracking positions "
                            "(window-bound claim)",
                            [f.id for f in cps])
    if _f(facts, "offset.position"):
        return StageVerdict("consumer_progress", Verdict.UNKNOWN, "consumer",
                            "positions exist but consumer progress missing")
    return StageVerdict("consumer_progress", Verdict.NOT_APPLICABLE,
                        "consumer", "no progress evidence")


def _stage_checkpoint(facts: list[Any]) -> StageVerdict:
    cps = _f(facts, "stream.checkpoint")
    if not cps:
        if _f(facts, "stream.progress") or _f(facts, "consumer.checkpoint"):
            return StageVerdict("checkpoint", Verdict.UNKNOWN, "stream",
                                "consumer/query progress but no checkpoint "
                                "metadata")
        return StageVerdict("checkpoint", Verdict.NOT_APPLICABLE, "stream",
                            "no checkpoint artifact")
    ev = [c.id for c in cps]
    for c in cps:
        if c.attrs.get("exists") is False:
            return StageVerdict("checkpoint", Verdict.DENY, "stream",
                                "checkpoint location absent/deleted", ev)
        if c.attrs.get("format_compatible") is False:
            return StageVerdict("checkpoint", Verdict.DENY, "stream",
                                "checkpoint incompatible after change "
                                "(reuse refused)", ev)
        if c.attrs.get("advancing") is False and _f(facts, "offset.position"):
            return StageVerdict("checkpoint", Verdict.DENY, "stream",
                                "checkpoint not advancing while source "
                                "advances", ev)
    return StageVerdict("checkpoint", Verdict.ALLOW, "stream",
                        "checkpoint present and advancing", ev)


def _stage_state_store(facts: list[Any]) -> StageVerdict:
    series = progress.progress_series(facts)
    growth = [f for f in series
              if isinstance(f.attrs.get("state_rows_total"), (int, float))]
    if len(growth) >= 3:
        rows = [f.attrs["state_rows_total"] for f in growth]
        if rows[-1] > rows[0] * 2 and rows == sorted(rows):
            return StageVerdict("state_store", Verdict.DENY, "stream",
                                "state rows monotonically growing across "
                                f"{len(rows)} batches "
                                f"({rows[0]} -> {rows[-1]})",
                                [f.id for f in growth])
    if _f(facts, "stream.progress"):
        return StageVerdict("state_store", Verdict.ALLOW, "stream",
                            "no unbounded state growth in observed window",
                            [f.id for f in series])
    return StageVerdict("state_store", Verdict.NOT_APPLICABLE, "stream",
                        "no progress events")


def _stage_schema(facts: list[Any]) -> StageVerdict:
    compat = correctness.schema_compatibility(facts)
    if compat["verdict"] == "breaking":
        return StageVerdict("schema", Verdict.DENY, "schema",
                            "breaking schema change: "
                            + "; ".join(compat.get("changes") or []),
                            compat["evidence"])
    if compat["verdict"] == "compatible":
        return StageVerdict("schema", Verdict.ALLOW, "schema",
                            "schema change compatible (additive/nullable)",
                            compat["evidence"])
    if _f(facts, "schema.version"):
        return StageVerdict("schema", Verdict.UNKNOWN, "schema",
                            "schema facts present but compatibility unknown",
                            compat["evidence"])
    return StageVerdict("schema", Verdict.NOT_APPLICABLE, "schema",
                        "no schema artifacts")


def _stage_spark_processing(facts: list[Any]) -> StageVerdict:
    series = progress.progress_series(facts)
    if not series:
        return StageVerdict("spark_processing", Verdict.NOT_APPLICABLE,
                            "stream", "no progress events")
    sustained, ev = progress.sustained_processing_deficit(series)
    if sustained:
        return StageVerdict("spark_processing", Verdict.DENY, "stream",
                            "sustained input>processing with backlog "
                            "growth", ev)
    return StageVerdict("spark_processing", Verdict.ALLOW, "stream",
                        "processing keeps up in the observed window",
                        [f.id for f in series[-2:]])


def _stage_sink(facts: list[Any]) -> StageVerdict:
    sinks = _f(facts, "stream.sink")
    if not sinks:
        return StageVerdict("sink", Verdict.NOT_APPLICABLE, "stream",
                            "no sink facts")
    bad = [s for s in sinks
           if str(s.attrs.get("status", "")).lower()
           in {"error", "failed", "stalled"} or s.attrs.get("error")]
    if bad:
        return StageVerdict("sink", Verdict.DENY, "stream",
                            "sink failing: " + "; ".join(
                                str(s.attrs.get("error")
                                    or s.attrs.get("status"))
                                for s in bad),
                            [s.id for s in bad])
    return StageVerdict("sink", Verdict.ALLOW, "stream",
                        "sink writing", [s.id for s in sinks])


# --- orchestrator ---------------------------------------------------------


def diagnose_stream(case: dict[str, Any], facts: list[Any]) -> StreamDiagnosis:
    name = str(case.get("name", ""))
    chain: list[StageVerdict] = []
    for fn in (_stage_auth, _stage_network, _stage_capacity,
               _stage_partitioning, _stage_consumer_group,
               _stage_consumer_progress, _stage_checkpoint,
               _stage_state_store, _stage_schema,
               _stage_spark_processing, _stage_sink):
        chain.append(fn(facts))
    # RTI sub-chain appended in order; verdict mapping: fail->DENY,
    # unknown->UNKNOWN, pass->ALLOW.
    for st in rti.evaluate_rti(facts):
        verdict = {"fail": Verdict.DENY, "unknown": Verdict.UNKNOWN,
                   "pass": Verdict.ALLOW}[st.verdict]
        chain.append(StageVerdict(st.layer, verdict, "fabric_rti",
                                  st.reason, st.evidence))

    findings: list[Finding] = []
    conflicts: list[str] = []

    # environment-scope contradiction -> cross_environment finding
    by_key: dict[str, dict[str, set[str]]] = {}
    for f in _f(facts, "environment.scope"):
        key = str(f.attrs.get("key"))
        by_key.setdefault(key, {}).setdefault(
            str(f.attrs.get("value")), set()).add(
                str(f.subject.get("source", "?")))
    env_conf = {k: v for k, v in by_key.items()
                if len(v) > 1 and k in {"tenant_id", "subscription_id",
                                        "namespace_id", "workspace_id"}}
    if env_conf:
        conflicts.append("environment mismatch: "
                         + "; ".join(sorted(env_conf)))
        findings.append(Finding(
            rule_id="SF-STR-ENV", title="Environment mismatch across "
            "streaming evidence", severity="P0", confidence="high",
            status="confirmed",
            subject={"case": name, "layer": "cross_environment"},
            evidence=[f.id for f in _f(facts, "environment.scope")
                      if str(f.attrs.get("key")) in env_conf],
            measured={"conflicting_keys":
                      {k: sorted(v) for k, v in env_conf.items()}},
            explanation="Artifacts disagree on environment identity; "
                        "evidence from different tenants/namespaces cannot "
                        "be merged into one authority story.",
            proposed_change=["Re-collect every artifact against the same "
                             "environment, then re-diagnose."],
            risks=["Findings may mix evidence from different "
                   "environments."]))

    # correctness semantics -> findings (never a verdict by themselves)
    delivery = correctness.classify_delivery(facts)
    if delivery["classification"] == "at_most_once_possible":
        findings.append(_mkfinding(
            "SF-STR-LOSS-RISK", "checkpoint", "Data-loss risk: checkpoint "
            "deleted with startingOffsets=latest", "P1", "high",
            delivery["evidence"],
            "Sem checkpoint e com start=latest, eventos anteriores não são "
            "replayable — perda é RISCO, não fato confirmado.",
            ["Restaurar checkpoint ou reprocessar a partir de posição "
             "explícita."],
            ["Reprocessamento pode duplicar saída em sink não-idempotente."]))
    elif delivery["classification"] == "at_least_once" and _f(
            facts, "stream.sink"):
        findings.append(_mkfinding(
            "SF-STR-DUP-RISK", "sink", "Duplicate risk: at-least-once "
            "pipeline with non-idempotent sink", "P2", "medium",
            delivery["evidence"],
            "Pipeline com replay + sink não idempotente: retry/replay pode "
            "duplicar — risco, não duplicatas confirmadas.",
            ["Tornar o sink idempotente (merge/dedup key) ou registrar "
             "semantics aceitas."],
            ["Duplicatas downstream em restart/replay."]))
    for cand in correctness.data_loss_candidates(facts):
        findings.append(_mkfinding(
            "SF-STR-RETENTION", "checkpoint", "Data-loss candidate: "
            + cand["kind"], "P1", "high", cand["evidence"],
            cand["explanation"],
            ["Aumentar retention ou corrigir checkpoint antes que a janela "
             "expire."],
            ["Eventos expirados não podem ser reprocessados."],
            measured={"kind": cand["kind"]}))
    # single-batch dip -> informational (explicitly NOT sustained lag)
    series = progress.progress_series(facts)
    if progress.single_batch_dip(series):
        findings.append(_mkfinding(
            "SF-STR-DIP", "spark_processing", "Single-batch processing dip "
            "— not sustained lag", "P3", "medium",
            [series[-1].id],
            "Somente o último batch processou abaixo do input; não é lag "
            "sustentado nem evidência de gargalo.",
            ["Observar a próxima janela antes de agir."],
            ["Reagir a um ponto único como se fosse trend."]))
    # watermark missing on stateful aggregation -> risk, never certainty
    has_state = any(f.attrs.get("state_rows_total") is not None
                    for f in series)
    wm_cfg = _f(facts, "stream.config")
    has_wm = any(f.attrs.get("watermark") for f in series) or any(
        c.subject.get("key") == "watermark" and c.attrs.get("value")
        for c in wm_cfg)
    if has_state and not has_wm:
        findings.append(_mkfinding(
            "SF-STR-WM", "state_store", "Stateful aggregation without "
            "watermark — state growth risk", "P2", "medium",
            [f.id for f in series if f.attrs.get("state_rows_total")
             is not None][:3],
            "Operador com estado sem watermark pode acumular estado "
            "indefinidamente — risco de crescimento, não falha garantida.",
            ["Adicionar withWatermark ou justificar TTL do estado."],
            ["OOM/estado sem bound em execução longa."]))

    denied = [s for s in chain if s.verdict is Verdict.DENY]
    unknown = [s for s in chain if s.verdict is Verdict.UNKNOWN]
    failure_layer = denied[0].layer if denied else None
    if env_conf:
        failure_layer = "cross_environment"
    status = ("denied" if denied else
              "unresolved" if unknown and not denied else "allowed")
    if not denied and not unknown:
        status = "allowed"
    return StreamDiagnosis(status=status, failure_layer=failure_layer,
                           chain=chain, findings=findings,
                           conflicts=conflicts, scenario=name,
                           delivery=delivery)


__all__ = ["StreamDiagnosis", "StageVerdict", "diagnose_stream"]
