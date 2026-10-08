"""TokenSave benchmark on a real case corpus (TOKENSAVE_PROOF, section 78).

Baseline is the naive agent: read every file of the case corpus into context
in full.  Each economy profile then runs ``TokenSave.context()`` on the same
task and its retrieval ledger reports *payload bytes delivered to context* --
never tokens.  Without a provider observation, ``tokens`` stays the literal
string ``"unresolved"`` (observed != estimated; unknown != zero).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sparkforge_azure.paths import WorkspaceScanPolicy, scan_repository
from sparkforge_azure.tokensave.engine import TokenSave

PROFILES = ("economy", "balanced", "deep")

# The case the vertical answers; terms the agent must ground.
DEFAULT_TASK = (
    "Meu job Azure Databricks nao consegue acessar a tabela/path "
    "abfss://lake@stg.dfs.core.windows.net/finance/orders governado por Unity "
    "Catalog — diagnostique a camada que nega para o principal spn-job-1 "
    "envolvendo loc_finance e cred_lake"
)
DEFAULT_TERMS = ["abfss", "spn-job-1", "loc_finance", "cred_lake"]


def corpus_files(case_dir: str | Path,
                 policy: WorkspaceScanPolicy | None = None) -> list[Path]:
    root = Path(case_dir).resolve()
    return sorted(scan_repository(root, policy or WorkspaceScanPolicy()).files)


def baseline_bytes(files: list[Path]) -> dict[str, Any]:
    """Naive agent = full read of the whole corpus into context."""
    sizes = {str(p): p.stat().st_size for p in files}
    return {"files": len(sizes), "bytes": sum(sizes.values()),
            "basis": "sum(stat().st_size) — leitura integral do corpus"}


def _profile_run(case_dir: Path, name: str, task: str,
                 terms: list[str], index_db: Path | None) -> dict[str, Any]:
    ts = TokenSave(case_dir, profile_name=name, index_db=index_db)
    result = ts.context(task, required_terms=terms)
    led = ts.ledger.summary()
    calls = led["calls"] or 1
    return {
        "status": result.status,
        "stop_reason": result.stop_reason,
        "levels_used": result.levels_used,
        "bytes_read": led["payload_bytes"],
        "payload_basis": led["payload_basis"],
        "level_distribution": led["bytes_by_level"],
        "calls": led["calls"],
        "full_read_rate": led["full_reads"] / calls,
        "cache_hit_rate": led["cache_hit_rate"],
        "context_reuse_rate": led["reuse_count"] / calls,
        "index_hit_rate": (
            led["expansion_count"] / calls if led["expansion_count"] else None
        ),
        "unresolved_terms": result.unresolved,
    }


def run_benchmark(case_dir: str | Path, *, task: str = DEFAULT_TASK,
                  required_terms: list[str] | None = None,
                  profiles: tuple[str, ...] = PROFILES,
                  index_db: str | Path | None = None) -> dict[str, Any]:
    """Baseline vs each profile on the same corpus — honest, measured metrics."""
    root = Path(case_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"case corpus not found: {case_dir}")
    files = corpus_files(root)
    base = baseline_bytes(files)
    terms = required_terms or list(DEFAULT_TERMS)
    idx = Path(index_db) if index_db else None
    out: dict[str, Any] = {
        "case_dir": str(root),
        "task": task,
        "required_terms": terms,
        "baseline": base,
        "profiles": {},
        # No provider usage observation exists in an offline benchmark.
        "tokens": "unresolved",
    }
    for name in profiles:
        run = _profile_run(root, name, task, terms, idx)
        run["bytes_avoided"] = base["bytes"] - run["bytes_read"]
        out["profiles"][name] = run
    return out


__all__ = ["DEFAULT_TASK", "DEFAULT_TERMS", "PROFILES", "baseline_bytes",
           "corpus_files", "run_benchmark"]
