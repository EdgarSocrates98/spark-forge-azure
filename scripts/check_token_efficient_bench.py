"""Validate the token-efficient benchmark registry without making claims.

Adapted from the AWS sibling: checks the suite declares baseline_id, non-empty
cases, exactly the economy/balanced/deep profiles, a benchmark gabarito whose
case ids match the suite's, and the decision-control-plane fixture with the
labeled-task floor. Also verifies every case ran against its expectation when
the matrix is executed (quality axes, not a score).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "token_efficient" / "suite.yaml"
PROFILES = {"economy", "balanced", "deep"}


def main() -> int:
    raw = yaml.safe_load(SUITE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        print("invalid benchmark schema_version")
        return 1
    baseline = raw.get("baseline_id")
    cases = raw.get("cases")
    if not isinstance(baseline, str) or not baseline or not isinstance(cases, list) or not cases:
        print("benchmark requires baseline_id and non-empty cases")
        return 1
    profiles = raw.get("profiles")
    if set(profiles or ()) != PROFILES:
        print("benchmark profiles must be economy, balanced and deep")
        return 1
    fixture_name = raw.get("benchmark_fixture") or raw.get("quality_fixture")
    fixture_path = SUITE.parent / str(fixture_name or "")
    if not fixture_path.is_file():
        print(f"benchmark fixture missing: {fixture_path}")
        return 1
    fixture = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    expected = (fixture or {}).get("cases") or []
    expected_ids = {str(c.get("id")) for c in expected if isinstance(c, dict)}
    suite_ids = {str(c.get("id")) for c in cases if isinstance(c, dict)}
    if suite_ids != expected_ids:
        print(f"case ids diverge suite<->gabarito: {sorted(suite_ids ^ expected_ids)}")
        return 1
    dcp = raw.get("decision_control_plane_fixture")
    if dcp:
        dcp_path = SUITE.parent / str(dcp)
        data = yaml.safe_load(dcp_path.read_text(encoding="utf-8")) if dcp_path.is_file() else {}
        labeled = sum(1 for c in data.get("cases", [])
                      if isinstance(c, dict) and str(c.get("label", "")).strip())
        if labeled < 50:
            print(f"decision_control_plane has {labeled} labeled tasks (<50)")
            return 1

    # A matriz inteira executa: cada celula confere status + eixos de qualidade
    # contra o gabarito. Sem score composto — recusar o gabarito e o defeito.
    import tempfile

    from sparkforge_azure.context.gateway import ContextGateway
    from sparkforge_azure.decision.cache import ArtifactCache
    from sparkforge_azure.evals.token_benchmark import (
        load_benchmark_suite,
        run_benchmark_matrix,
    )
    from sparkforge_azure.mcp.tools import full_catalog

    suite = load_benchmark_suite(SUITE.parent)
    with tempfile.TemporaryDirectory(
        prefix="sfa-bench-", ignore_cleanup_errors=True
    ) as tmp:
        # Cache isolado: o benchmark nao pode gravar .sparkforge-azure/ na
        # arvore nem ler hit de execucao anterior (contaminaria a medicao).
        gateway = ContextGateway(full_catalog(), cache=ArtifactCache(cache_dir=tmp))
        matrix = run_benchmark_matrix(suite, gateway=gateway)
    failed = [r for r in matrix["results"] if r.get("passed") is not True]
    unresolved_tokens = sum(
        1 for r in matrix["results"] if r.get("tokens_unresolved")
    )
    total = len(matrix["results"])
    if failed:
        for r in failed[:10]:
            print(
                f"FAIL {r['case_id']}@{r['profile']}: status={r.get('status')} "
                f"refusal={r.get('refusal_reason')}"
            )
        return 1
    print(
        f"token-efficient bench: {total}/{total} celulas ok "
        f"({len(cases)} casos x {len(profiles)} profiles); "
        f"tokens_unresolved={unresolved_tokens} (sem provider — declarado, nao zero)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
