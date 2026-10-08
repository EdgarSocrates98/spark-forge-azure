"""Migration planner — waves, cycles, rollback (SDD MIGRATION_PLANNER).

Waves follow the dependency graph's topological order.  A dependency cycle
is REVIEW — never a fabricated order (prompt §133/scenario 14).  Every wave
carries a receipt and an explicit rollback plan (§140-142): trigger,
steps, and the data-divergence policy.
"""
from __future__ import annotations

from typing import Any


def _facts(facts: list[Any], kind: str) -> list[Any]:
    return [f for f in facts if f.kind == kind]


def _asset_id(f: Any) -> str:
    return str(next(iter(f.subject.values())))


def _deps(facts: list[Any]) -> dict[str, set[str]]:
    """depends_on multimap: src -> {dst} — an asset may depend on many."""
    deps: dict[str, set[str]] = {}
    for e in _facts(facts, "dep.edge"):
        if e.subject.get("relation") == "depends_on":
            deps.setdefault(str(e.subject["src"]), set()).add(
                str(e.subject["dst"]))
    return deps


def plan_waves(facts: list[Any],
               readiness: dict[str, str]) -> dict[str, Any]:
    """Topological waves over migratable assets.

    An edge src --depends_on--> dst means dst must migrate in an earlier
    or equal wave.  BLOCKED/MANUAL/UNRESOLVED assets are never placed in
    a wave — they surface in ``pending`` with their reason.
    """
    deps = _deps(facts)
    assets = {_asset_id(f): f for f in facts
              if f.kind.startswith("mig.")
              and f.kind not in {"mig.assessment_result", "mig.validation"}
              and not f.kind.endswith(".table")}
    migratable = {a for a in assets
                  if str(readiness.get(a, "UNRESOLVED")) in
                  {"READY", "REVIEW"}}
    pending = {a: str(readiness.get(a, "UNRESOLVED"))
               for a in assets if a not in migratable}

    cycle_nodes = _find_cycle(deps, set(assets) | set(deps)
                              | {d for ds in deps.values() for d in ds})
    if cycle_nodes:
        return {
            "status": "REVIEW",
            "reason": "migration dependency cycle — REVIEW, ordem nunca "
                      "fabricada",
            "cycle": sorted(cycle_nodes),
            "waves": [],
            "pending": pending,
        }

    waves: list[dict[str, Any]] = []
    placed: set[str] = set()
    remaining = set(migratable)
    while remaining:
        ready_now = sorted(
            a for a in remaining
            if all(p in placed or p not in assets
                   for p in deps.get(a, ())))
        if not ready_now:  # defensive; cycle check above should catch it
            return {"status": "REVIEW",
                    "reason": "unschedulable remainder",
                    "cycle": sorted(remaining),
                    "waves": waves, "pending": pending}
        waves.append({
            "wave": len(waves) + 1,
            "assets": ready_now,
            "rollback": {
                "trigger": "validation FAIL ou regression observada",
                "steps": ["desativar trigger target",
                          "reativar pipeline source",
                          "redirecionar consumidores para source"],
                "data_divergence_policy": "freeze durante parallel-run; "
                                          "divergencia reconciliada antes "
                                          "do cutover",
            },
            "receipt": {"asset_count": len(ready_now),
                        "cutover": "parallel_run->shadow->cutover"},
        })
        placed.update(ready_now)
        remaining -= set(ready_now)
    return {"status": "ok", "waves": waves, "wave_count": len(waves),
            "pending": pending, "cycle": []}


def _find_cycle(deps: dict[str, set[str]], nodes: set[str]) -> set[str]:
    """DFS cycle detection over the depends_on graph."""
    perm: set[str] = set()
    temp: set[str] = set()
    cycle: set[str] = set()

    def visit(n: str, stack: tuple[str, ...]) -> None:
        if n in perm:
            return
        if n in temp:
            cycle.update(stack[stack.index(n):])
            cycle.add(n)
            return
        temp.add(n)
        for dst in sorted(deps.get(n, ())):
            if dst in nodes:
                visit(dst, stack + (n,))
        temp.discard(n)
        perm.add(n)

    for n in sorted(nodes):
        visit(n, ())
    return cycle


def shared_upstream_blockers(facts: list[Any],
                             readiness: dict[str, str]) -> list[dict[str, Any]]:
    """A wave candidate blocked by a shared upstream asset (scenario 15):
    an asset whose upstream dependency is itself not READY/REVIEW."""
    out = []
    for src, dsts in sorted(_deps(facts).items()):
        if str(readiness.get(src)) not in {"READY", "REVIEW"}:
            continue
        for dst in sorted(dsts):
            state = str(readiness.get(dst, "UNRESOLVED"))
            if state in {"BLOCKED", "MANUAL", "UNRESOLVED"}:
                out.append({"asset": src, "blocked_by": dst,
                            "upstream_state": state})
    return out


__all__ = ["plan_waves", "shared_upstream_blockers"]
