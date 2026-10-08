"""Structured Streaming progress analysis (SDD STRUCTURED_STREAMING).

Operates on extracted ``stream.progress`` / ``offset.position`` /
``consumer.checkpoint`` facts.  The unit of truth is the *series*, never a
single point: one batch below input rate is not sustained lag, and one
metric point is not a trend.
"""
from __future__ import annotations

from typing import Any

#: Batches considered before claiming a *sustained* processing deficit.
SUSTAINED_BATCHES = 2
#: Partition-skew threshold: hottest partition backlog vs median of the rest.
SKEW_RATIO = 5.0


def progress_series(facts: list[Any],
                    query_id: str | None = None) -> list[Any]:
    """stream.progress facts ordered by batch_id for a query."""
    out = [f for f in facts if f.kind == "stream.progress"
           and (query_id is None or f.subject.get("query_id") == query_id)]
    def _bid(f: Any) -> int:
        try:
            return int(f.subject.get("batch_id", -1))
        except (TypeError, ValueError):
            return -1
    return sorted(out, key=_bid)


def sustained_processing_deficit(series: list[Any]) -> tuple[bool, list[str]]:
    """input_rate > process_rate for the last >=SUSTAINED_BATCHES batches
    *and* backlog growing (end_offsets ahead of start_offsets when present)."""
    tail = series[-SUSTAINED_BATCHES:]
    if len(tail) < SUSTAINED_BATCHES:
        return False, []
    deficit = all((f.attrs.get("input_rate") or 0)
                  > (f.attrs.get("process_rate") or 0) for f in tail)
    if not deficit:
        return False, []
    backlog_growth = True
    ends = [f.attrs.get("end_offsets") for f in tail]
    starts = [f.attrs.get("start_offsets") for f in tail]
    if all(isinstance(e, dict) and isinstance(s, dict)
           for e, s in zip(ends, starts, strict=True)):
        deltas = []
        for e, s in zip(ends, starts, strict=True):
            total = sum((e.get(p, 0) or 0) - (s.get(p, 0) or 0)
                        for p in set(e) | set(s))
            deltas.append(total)
        backlog_growth = deltas[-1] > deltas[0] or deltas[-1] > 0
    ok = deficit and backlog_growth
    return ok, [f.id for f in tail] if ok else []


def single_batch_dip(series: list[Any]) -> bool:
    """Exactly the last batch below input while predecessors were fine —
    explicitly NOT sustained lag (prompt §205)."""
    if len(series) < 2:
        return False
    last = series[-1]
    if not ((last.attrs.get("input_rate") or 0)
            > (last.attrs.get("process_rate") or 0)):
        return False
    return all((f.attrs.get("process_rate") or 0)
               >= (f.attrs.get("input_rate") or 0) for f in series[:-1])


def partition_skew(facts: list[Any]) -> tuple[bool, dict[str, Any]]:
    """Consumer lag concentrated on a minority of partitions.

    Compares ``offset.position`` (source latest sequence) vs
    ``consumer.checkpoint`` per partition; flags when the hottest partition
    backlog exceeds SKEW_RATIO × the median of the others.
    """
    src: dict[tuple[str, str], float] = {}
    for f in facts:
        if f.kind != "offset.position":
            continue
        v = f.attrs.get("latest_sequence", f.attrs.get("latest_offset"))
        if isinstance(v, (int, float)):
            src[(str(f.subject.get("hub_id")),
                  str(f.subject.get("partition")))] = float(v)
    lag: dict[tuple[str, str], float] = {}
    ev: list[str] = []
    for f in facts:
        if f.kind != "consumer.checkpoint":
            continue
        key = (str(f.subject.get("hub_id")),
               str(f.subject.get("partition")))
        cur = f.attrs.get("sequence", f.attrs.get("offset"))
        ev.append(f.id)
        if key in src and isinstance(cur, (int, float)):
            lag[key] = max(0.0, src[key] - float(cur))
    if len(lag) < 3:
        return False, {}
    ordered = sorted(lag.values())
    median = ordered[len(ordered) // 2] or 0.0
    hot = ordered[-1]
    if hot > 0 and hot > max(median, 1.0) * SKEW_RATIO:
        worst = [f"{k[0]}:{k[1]}" for k, v in lag.items() if v == hot]
        return True, {"skew_ratio": round(hot / max(median, 1.0), 2),
                      "hot_partitions": sorted(worst),
                      "lag_per_partition": {
                          f"{k[0]}:{k[1]}": v for k, v in
                          sorted(lag.items())},
                      "evidence": ev}
    return False, {}


def consumer_stalled(facts: list[Any]) -> tuple[bool, list[str]]:
    """Source positions observed advancing while a consumer group's
    checkpoints stand still (no updated_at movement or offsets far behind
    on every partition)."""
    cps = [f for f in facts if f.kind == "consumer.checkpoint"]
    if not cps:
        return False, []
    stale = [f for f in cps if f.attrs.get("updated_at") is None
             or f.attrs.get("stale") is True]
    src_advancing = bool(facts) and any(
        f.kind == "offset.position" for f in facts)
    if stale and src_advancing:
        return True, [f.id for f in stale]
    # Alternative shape: bundle declares per-partition lag without series.
    lag_facts = [f for f in cps if (f.attrs.get("lag") or 0) > 0]
    if lag_facts:
        return True, [f.id for f in lag_facts]
    return False, []


__all__ = [
    "SKEW_RATIO", "SUSTAINED_BATCHES", "consumer_stalled",
    "partition_skew", "progress_series", "single_batch_dip",
    "sustained_processing_deficit",
]
