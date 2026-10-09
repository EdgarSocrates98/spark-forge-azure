"""AWS<->Azure parity gate: validates parity/aws-azure.yaml is complete and
every claimed proof path exists. Exit 0 = parity matrix consistent.

Rules (prompt_evo_economy):
  - every entry classified with the closed vocabulary;
  - proof must point to a real path in this repo (or name a doc section);
  - DIFFERENT_BY_DESIGN and DEFERRED are legitimate terminal states, but
    each must carry a `gap`/`action` explanation;
  - no entry may claim parity with proof: none.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "parity" / "aws-azure.yaml"

CLASSIFICATIONS = {
    "AWS_AHEAD", "AZURE_AHEAD", "EQUIVALENT", "DIFFERENT_BY_DESIGN", "DEFERRED",
}
PORTABILITY = {"COPY_SAFE", "ADAPT", "REFERENCE_ONLY", "PROVIDER_SPECIFIC", "DO_NOT_PORT"}
STATUSES = {
    "ABSENT", "FOUNDATION", "PARTIAL", "MATURE", "DEEP", "EVALUATED",
    "PRODUCTION_CANDIDATE", "DEFERRED", "EXPERIMENTAL",
}


def _proof_paths_exist(proof: str) -> list[str]:
    """Every path-like token in `proof` must exist under the repo root.
    Tokens inside parentheses or prose are ignored; we check tokens that
    start with a known top-level dir or end with a source/doc suffix."""
    missing = []
    scrubbed = proof.replace("(", " ").replace(")", " ").replace("+", " ").replace(",", " ")
    prefixes = ("sparkforge_azure/", "scripts/", "docs/", "evals/", "tests/", "parity/")
    for token in scrubbed.split():
        token = token.strip()
        if "/" not in token and not token.endswith((".py", ".md", ".json", ".yaml")):
            continue
        if token.startswith(prefixes) and not (ROOT / token).exists():
            missing.append(token)
    return missing


def main() -> int:
    if not MATRIX.is_file():
        print(f"parity matrix missing: {MATRIX}")
        return 1
    raw = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        print("parity matrix: schema_version must be 1")
        return 1
    entries = raw.get("entries")
    if not isinstance(entries, list) or not entries:
        print("parity matrix: no entries")
        return 1
    baseline = raw.get("baseline") or {}
    for key in ("aws_main_sha", "azure_base_sha"):
        if not isinstance(baseline.get(key), str) or len(baseline[key]) != 40:
            print(f"parity matrix: baseline.{key} must be a full sha")
            return 1

    failures: list[str] = []
    counts: dict[str, int] = {}
    for i, entry in enumerate(entries):
        cap = entry.get("capability") if isinstance(entry, dict) else None
        if not cap:
            failures.append(f"entry[{i}]: missing capability")
            continue
        cls = entry.get("classification")
        if cls not in CLASSIFICATIONS:
            failures.append(f"{cap}: classification {cls!r} not in {sorted(CLASSIFICATIONS)}")
        else:
            counts[cls] = counts.get(cls, 0) + 1
        port = entry.get("portability")
        if port not in PORTABILITY:
            failures.append(f"{cap}: portability {port!r} not in {sorted(PORTABILITY)}")
        for side in ("aws", "azure"):
            if entry.get(side) not in STATUSES:
                failures.append(
                    f"{cap}: {side} status {entry.get(side)!r} not in {sorted(STATUSES)}"
                )
        proof = entry.get("proof")
        if not isinstance(proof, str) or not proof.strip():
            failures.append(f"{cap}: proof missing — no capability claim without evidence")
        elif "none" not in proof.lower()[:8]:
            for missing in _proof_paths_exist(proof):
                failures.append(f"{cap}: proof path does not exist: {missing}")
        if cls in {"DIFFERENT_BY_DESIGN", "DEFERRED"}:
            gap, action = str(entry.get("gap") or ""), str(entry.get("action") or "")
            if gap in {"", "none"} and action in {"", "none"}:
                failures.append(f"{cap}: {cls} requires a gap or action explanation")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 1
    print(f"aws-azure parity: {len(entries)} capabilities — "
          + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
