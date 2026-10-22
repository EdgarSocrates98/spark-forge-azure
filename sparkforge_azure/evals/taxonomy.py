"""§7.1 taxonomy of the eval corpus — the classified inventory that the
``forge/context/v1`` manifest persists (``eval_suites[].kind`` +
``capabilities.evals.detail``) and that ``sparkforge-azure evals`` serves.

One entry per declared suite. Fields:

* ``kind`` — the closed ``_forgecontext.EVAL_KINDS`` enum, i.e. the four
  §7.1 categories: ``developer``, ``runtime-decision``,
  ``output-verification``, ``host-conformance``.
* ``sealed`` — §7.3: expected answers must NEVER reach the executing
  agent's surface. ``describe``/``list`` emit metadata and an integrity
  hash, never answer content. The strict case (``evals/agentic/`` and
  ``evals/agent_runtime/expected/``) never echoes gabarito bytes.
* ``environment`` — what a green run proves (§7.3, simulated != real):
  ``deterministic`` (offline recompute of the engine — proves code, not a
  live environment), ``host`` (a real host agent must execute; the CLI
  refuses to impersonate it — executor != evaluator).
* ``run`` — how ``evals run`` executes the suite:

    - ``{"kind": "script", "path": ...}`` — a repo gate
      (``python <path>``); refused ``unavailable`` outside the checkout
      because scripts/ and evals/ runners are not packaged;
    - ``{"kind": "pytest", "path": ...}`` — a pytest gate, same rule;
    - ``{"kind": "native", "name": ...}`` — an in-process runner of
      ``sparkforge_azure.evals.surface``;
    - ``None`` — either a host agent must execute it
      (``EVALS-REQUIRES-HOST``) or the suite is corpus/baseline data with
      no standalone runner (``EVALS-RUNNER-UNAVAILABLE``).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

_REPO_DIR = Path(__file__).resolve().parents[2]

KINDS: tuple[str, ...] = (
    "developer",
    "runtime-decision",
    "output-verification",
    "host-conformance",
)

# Named refusal codes — one per refusal class, greppable, the house pattern.
E_SUITE = "EVALS-SUITE-UNKNOWN"
E_HOST = "EVALS-REQUIRES-HOST"
E_UNAVAILABLE = "EVALS-RUNNER-UNAVAILABLE"

SUITES: tuple[dict[str, Any], ...] = (
    {
        "id": "agentic-sdd",
        "kind": "host-conformance",
        "location": "evals/agentic/sdd",
        "environment": "host",
        "sealed": True,
        "run": None,
        "runner_label": (
            "scripts/run_agentic_eval.py --suite sdd + "
            "`python -m sparkforge_azure.evals grade`"
        ),
        "description": (
            "agentic SDD suite: contract-prepared workspaces under "
            "evals/agentic/sdd, executed by a host agent and graded "
            "against sha256-pinned baselines/"
        ),
    },
    {
        "id": "agent-runtime",
        "kind": "runtime-decision",
        "location": "evals/agent_runtime",
        "environment": "deterministic",
        "sealed": True,
        "run": {"kind": "native", "name": "agent-runtime"},
        "runner_label": "in-process: agent_eval.evaluate_case (configs A-D)",
        "description": (
            "runtime decision contracts: required/forbidden findings and "
            "known_unresolved per case, measured across the A-D "
            "configurations; host transcripts produce the *.host.json "
            "receipts next to the deterministic reports"
        ),
    },
    {
        "id": "agents-routes",
        "kind": "developer",
        "location": "evals/agents",
        "environment": "deterministic",
        "sealed": True,
        "run": {"kind": "pytest", "path": "tests/test_agent_eval_cases.py"},
        "runner_label": "pytest tests/test_agent_eval_cases.py",
        "description": (
            "route_positive/route_negative cases per specialist run "
            "against the real router — internal routing quality of the "
            "agent roster"
        ),
    },
    {
        "id": "convergence",
        "kind": "output-verification",
        "location": "evals/convergence",
        "environment": "deterministic",
        "sealed": True,
        "run": {
            "kind": "script",
            "path": "evals/convergence/runner.py",
            "args": ["--json"],
        },
        "runner_label": "python evals/convergence/runner.py --json",
        "description": (
            "cross-vertical convergence: the same case through "
            "databricks/fabric/stream/migration pipelines must emit a "
            "consistent result contract"
        ),
    },
    {
        "id": "host-proof",
        "kind": "host-conformance",
        "location": "evals/host_proof",
        "environment": "host",
        "sealed": False,
        "run": None,
        "runner_label": "host adapter proof run (claude -p) + committed receipts",
        "description": (
            "real-host proof receipts (trace_ref, measured usage, "
            "proof_kind) — evidence that the runtime adapter executed on a "
            "live host, not a simulation"
        ),
    },
    {
        "id": "mcp-conformance",
        "kind": "host-conformance",
        "location": "evals/mcp-conformance/matrix.yaml",
        "environment": "deterministic",
        "sealed": False,
        "run": {"kind": "pytest", "path": "tests/test_mcp_conformance_matrix.py"},
        "runner_label": "pytest tests/test_mcp_conformance_matrix.py",
        "description": (
            "MCP spec requirement -> versioned evidence matrix; unresolved "
            "rows stay visible, never silently passed"
        ),
    },
    {
        "id": "parity",
        "kind": "developer",
        "location": "evals/parity",
        "environment": "deterministic",
        "sealed": True,
        "run": None,
        "runner_label": (
            "corpus: sbom.cdx.json + token_benchmark_baseline.json — "
            "consumed by scripts/check_token_efficient_bench.py and "
            "scripts/check_aws_parity.py"
        ),
        "description": (
            "parity corpus: the token benchmark gabarito and the supply "
            "SBOM; protected by hash, compared by the bench gate"
        ),
    },
    {
        "id": "portability",
        "kind": "developer",
        "location": "evals/portability",
        "environment": "deterministic",
        "sealed": True,
        "run": {
            "kind": "script",
            "path": "evals/portability/runner.py",
            "args": ["--json"],
        },
        "runner_label": "python evals/portability/runner.py --json",
        "description": (
            "portability matrix: detach/relocate/transitive-deps cases run "
            "in temp dirs with redirected HOME/XDG — global pollution fails "
            "the case"
        ),
    },
    {
        "id": "token-efficient",
        "kind": "developer",
        "location": "evals/token_efficient",
        "environment": "deterministic",
        "sealed": True,
        "run": {"kind": "script", "path": "scripts/check_token_efficient_bench.py"},
        "runner_label": "python scripts/check_token_efficient_bench.py",
        "description": (
            "economy/balanced/deep profile matrix of the Context Gateway; "
            "provider tokens stay unresolved without a host transcript"
        ),
    },
)


class TaxonomyError(ValueError):
    """Named refusal: message already carries the ``EVALS-*`` code."""


def catalog() -> list[dict[str, Any]]:
    return [dict(s) for s in SUITES]


def suite_ids() -> list[str]:
    return [s["id"] for s in SUITES]


def get(suite_id: str) -> dict[str, Any]:
    for s in SUITES:
        if s["id"] == suite_id:
            return dict(s)
    raise TaxonomyError(
        f"{E_SUITE}: suite {suite_id!r} desconhecida; declaradas: {', '.join(suite_ids())}"
    )


def kind_counts() -> dict[str, int]:
    counts = {k: 0 for k in KINDS}
    for s in SUITES:
        counts[s["kind"]] += 1
    return counts


def capability_detail() -> str:
    """The one-line ``capabilities.evals.detail`` persisted in the manifest —
    the §7.1 classification summary plus the §7.3 posture."""
    counts = kind_counts()
    parts = ", ".join(f"{k}={counts[k]}" for k in KINDS)
    return (
        f"categories: {parts}; sealed expected answers never reach agent "
        "surfaces (evals describe emits hashes, never answers); "
        "deterministic proofs are not real-environment proof"
    )


def _repo_path(location: str) -> Path | None:
    p = _REPO_DIR / location
    return p if p.exists() else None


def suite_sha256(suite: dict[str, Any]) -> str | None:
    """sha256 over every file under the suite location — the tamper-evident
    baseline/answer hash (§7.3 'preserve hashes'). ``os.walk``, not
    ``Path.rglob``: the raw-glob gate in tests/ scans for glob calls, and
    this walk is over dirs this repo owns and versions.

    ``None`` when the location is absent (packaged installs ship the
    bundled groups, not the dev corpus) — the caller reports
    ``unresolved``, never a silent omission."""
    base = _repo_path(suite["location"])
    if base is None:
        return None
    h = hashlib.sha256()
    if base.is_file():
        h.update(base.name.encode("utf-8"))
        h.update(b"\0")
        h.update(base.read_bytes())
        return h.hexdigest()
    for root, dirs, files in os.walk(base):
        dirs.sort()
        for name in sorted(files):
            p = Path(root) / name
            if not p.is_file():
                continue
            h.update(p.relative_to(base).as_posix().encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()


def describe(suite_id: str) -> dict[str, Any]:
    """evals.describe — metadata only. §7.3: sealed suites expose the answer
    location CLASS and the integrity hash, never answer content. The
    exposure test greps this payload for gabarito bytes and must find
    none."""
    s = get(suite_id)
    digest = suite_sha256(s)
    return {
        "id": s["id"],
        "kind": s["kind"],
        "location": s["location"],
        "environment": s["environment"],
        "sealed": s["sealed"],
        "expected_answers": (
            "sealed — never emitted to executing agents" if s["sealed"] else "not sealed"
        ),
        "integrity": {
            "algorithm": "sha256",
            "suite_sha256": digest if digest is not None else "unresolved",
        },
        "runner": s["runner_label"],
        "runnable_by_cli": s["run"] is not None,
        "description": s["description"],
        "proof": (
            "host-required (real environment)"
            if s["environment"] == "host"
            else f"{s['environment']} — not real-environment proof"
        ),
    }


def listing() -> dict[str, Any]:
    """evals.list — the classified inventory with per-kind counts."""
    return {
        "schema": "sparkforge-azure/evals-list/v1",
        "categories": list(KINDS),
        "counts": kind_counts(),
        "suites": [
            {
                "id": s["id"],
                "kind": s["kind"],
                "environment": s["environment"],
                "sealed": s["sealed"],
                "runnable_by_cli": s["run"] is not None,
            }
            for s in SUITES
        ],
    }


def manifest_suites(cli: str) -> list[dict[str, Any]]:
    """The ``eval_suites`` of forge/context/v1 — the §7.1 classification in
    the closed (id, kind, command) shape. ``command`` is the read-only
    describe verb: a consumer can always inspect what a suite is."""
    return [
        {
            "id": s["id"],
            "kind": s["kind"],
            "command": [cli, "evals", "describe", "--suite", s["id"]],
        }
        for s in SUITES
    ]


__all__ = [
    "E_HOST",
    "E_SUITE",
    "E_UNAVAILABLE",
    "KINDS",
    "SUITES",
    "TaxonomyError",
    "capability_detail",
    "catalog",
    "describe",
    "get",
    "kind_counts",
    "listing",
    "manifest_suites",
    "suite_ids",
    "suite_sha256",
]
