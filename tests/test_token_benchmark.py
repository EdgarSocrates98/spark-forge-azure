"""Token-efficient benchmark matrix (evals/token_benchmark.py).

Mesmo contrato do irmao AWS: casos identicos nos tres profiles, eixos crus,
sem score composto, tokens_unresolved declarado sem provider.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sparkforge_azure.context.gateway import ContextGateway
from sparkforge_azure.decision.cache import ArtifactCache
from sparkforge_azure.evals.token_benchmark import (
    compare_benchmark_matrix,
    load_benchmark_suite,
    run_benchmark_matrix,
)
from sparkforge_azure.mcp.tools import full_catalog

SUITE_DIR = Path("evals/token_efficient")


@pytest.fixture(scope="module")
def suite():
    return load_benchmark_suite(SUITE_DIR)


@pytest.fixture(scope="module")
def matrix(suite, tmp_path_factory):
    # O gateway persiste context_ref em state_dir()/cache por default — sob
    # teste, isole em tmp_path para nao vazar .sparkforge-azure/ na arvore.
    cache = ArtifactCache(cache_dir=tmp_path_factory.mktemp("bench-cache"))
    gateway = ContextGateway(full_catalog(), cache=cache)
    return run_benchmark_matrix(suite, gateway=gateway)


def test_suite_loads_with_sha_and_replay_contract(suite):
    assert suite["id"] == "token-efficient-matrix"
    assert len(suite["sha256"]) == 64
    assert len(suite["cases"]) == 15
    contract = suite["decision_replay_contract"]
    assert contract["labeled_tasks"] >= contract["minimum_labeled_tasks"]
    assert contract["same_case_required"] is True
    assert contract["cost_requires_basis"] is True


def test_matrix_covers_every_case_and_profile(matrix):
    seen = {(r["case_id"], r["profile"]) for r in matrix["results"]}
    assert len(seen) == 45  # 15 casos x 3 profiles
    assert {p for _, p in seen} == {"economy", "balanced", "deep"}


def test_every_cell_matches_its_gabarito(matrix):
    failed = [r for r in matrix["results"] if r["passed"] is not True]
    assert failed == []


def test_profiles_differ_only_where_escalation_is_allowed(matrix):
    plans = matrix["summary"]
    # deep permite escalacao agentica; economy/balanced nao.
    assert plans["deep"]["execution_plan"].get("debate", 0) >= 1
    assert plans["economy"]["execution_plan"].get("debate", 0) == 0
    assert plans["balanced"]["execution_plan"].get("reviewer", 0) == 0


def test_tokens_are_unresolved_not_zero_without_provider(matrix):
    assert all(r["tokens_unresolved"] for r in matrix["results"])
    assert all(r["provider_tokens"] is None for r in matrix["results"])


def test_compare_identical_matrix_is_stable(matrix):
    diff = compare_benchmark_matrix(matrix, matrix)
    assert "refused" not in diff
    assert len(diff["cells"]) == 45
    assert all(c["payload_bytes"]["delta"] == 0 for c in diff["cells"])


def test_compare_refuses_on_mismatch(matrix):
    refused = compare_benchmark_matrix(matrix, {"suite": {"id": "x"}, "results": []})
    assert refused["refused"]["reason"] == "suite_mismatch"
