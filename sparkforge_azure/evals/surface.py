"""The ``sparkforge-azure evals`` surface — §7.2 ops ``evals.list``,
``evals.describe``, ``evals.run``, ``evals.result`` over the classified
taxonomy of ``sparkforge_azure.evals.taxonomy``.

Security contract (§7.3), enforced here and tested in
``tests/test_evals_surface.py``:

* sealed expected answers are NEVER emitted — ``list``/``describe`` carry
  counts, locations and an integrity hash only;
* suites a host must execute refuse ``EVALS-REQUIRES-HOST`` instead of
  being impersonated by the CLI — the executor and the evaluator are
  different actors;
* every run result marks ``environment`` — ``deterministic`` is never
  reported as real-environment proof.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from sparkforge_azure.evals import taxonomy

_REPO_DIR = Path(__file__).resolve().parents[2]

# Run dir names: first char alnum, then word chars/dots/dashes — no
# separators, no ``..`` escape, no absolute paths (§13.1).
_SAFE_RUN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Timeout for delegated gates — deterministic, bounded, never a hang.
_RUN_TIMEOUT_S = 300


def _envelope(suite: dict[str, Any], **extra: Any) -> dict[str, Any]:
    """Every result carries the §7.3 markers: what environment proved it and
    whether the answers stay sealed."""
    return {
        "schema": "sparkforge-azure/evals-run/v1",
        "suite": suite["id"],
        "kind": suite["kind"],
        "environment": suite["environment"],
        "real_environment_proof": suite["environment"] == "host",
        "sealed": suite["sealed"],
        **extra,
    }


def run(suite_id: str) -> dict[str, Any]:
    """evals.run — dispatch to the suite's declared runner.

    Host-required suites are a named refusal, not a synthetic execution:
    the suite measures a host agent, and a CLI that faked the run would be
    the evaluator impersonating the executor (§7.3). Corpus suites
    (``parity``) have no standalone runner — also a named refusal, not a
    silent pass."""
    s = taxonomy.get(suite_id)
    spec = s["run"]
    if spec is None:
        if s["environment"] == "host":
            raise taxonomy.TaxonomyError(
                f"{taxonomy.E_HOST}: suite {suite_id!r} mede um agente de "
                "host; a CLI nao a executa (executor != avaliador). "
                f"Execute no host e pontue com `{s['runner_label']}`"
            )
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: suite {suite_id!r} e corpus/"
            f"baseline — sem runner proprio; verificada via {s['runner_label']}"
        )
    kind = spec["kind"]
    if kind == "native":
        return _envelope(s, **_run_native(spec["name"], s))
    if kind in ("script", "pytest"):
        return _envelope(s, **_run_delegated(spec, s))
    raise taxonomy.TaxonomyError(
        f"{taxonomy.E_UNAVAILABLE}: runner kind {kind!r} desconhecido para {suite_id!r}"
    )


def _run_native(name: str, suite: dict[str, Any]) -> dict[str, Any]:
    if name == "agent-runtime":
        return _run_agent_runtime(suite)
    raise taxonomy.TaxonomyError(
        f"{taxonomy.E_UNAVAILABLE}: runner nativo {name!r} desconhecido"
    )


def _run_delegated(spec: dict[str, Any], suite: dict[str, Any]) -> dict[str, Any]:
    """script/pytest gates run as documented: the same argv a developer
    types, in a subprocess, captured and bounded. Outside the checkout the
    file is absent and the refusal is named — an installed wheel honestly
    reports the gate as ``unavailable`` instead of inventing a verdict."""
    path = _REPO_DIR / spec["path"]
    if not path.is_file():
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: {spec['path']} so existe no checkout; "
            "o pacote instalado nao carrega os gates de desenvolvimento"
        )
    if spec["kind"] == "pytest":
        argv = [sys.executable, "-m", "pytest", spec["path"], "-q"]
    else:
        args = [a.replace("{location}", suite["location"]) for a in spec.get("args", ())]
        argv = [sys.executable, spec["path"], *args]
    proc = subprocess.run(  # noqa: S603 — argv e a spec declarada da suite (sys.executable + arquivo versionado)
        argv,
        cwd=_REPO_DIR,
        capture_output=True,
        text=True,
        timeout=_RUN_TIMEOUT_S,
        check=False,
    )
    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "exit_code": proc.returncode,
        "runner": spec["path"],
        "output_tail": (proc.stdout + proc.stderr).strip()[-2000:],
    }


def _run_agent_runtime(suite: dict[str, Any]) -> dict[str, Any]:
    """Recompute each agent_runtime case in-process
    (``agent_eval.evaluate_case`` — configs A-D on the deterministic
    GENERIC runtime) and report per-case verdicts. The report carries
    quality hits/misses and necessity classes — never the expected/
    gabarito payload itself."""
    import yaml

    from sparkforge_azure.agentic.agent_eval import evaluate_case

    base = _REPO_DIR / suite["location"]
    cases_dir = base / "cases"
    if not cases_dir.is_dir():
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: {suite['location']}/cases ausente "
            "(o corpus vive no checkout, nao no wheel)"
        )
    results: list[dict[str, Any]] = []
    failures = 0
    for case_path in sorted(cases_dir.glob("*.yaml")):
        case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
        expected_path = base / "expected" / f"{case['id']}.yaml"
        if not expected_path.is_file():
            results.append(
                {"case": case["id"], "status": "unresolved", "detail": "expected ausente"}
            )
            failures += 1
            continue
        out = evaluate_case(case_path, root=_REPO_DIR)
        baseline = out["results"]["A"]
        quality = baseline["quality"]
        # Contrato de decisao do runtime: nunca emitir finding proibido e
        # preservar o que o caso declara nao-resolvido. `degraded` e o
        # estado esperado do runtime GENERIC (agentes simulados) — nao e
        # falha; a falha e violar o contrato do expected/.
        ok = (
            quality["forbidden_findings_hit"] == 0
            and quality["known_unresolved_preserved"]
            == quality["known_unresolved_total"]
        )
        results.append(
            {
                "case": case["id"],
                "status": "pass" if ok else "fail",
                "required_findings_hit": quality["required_findings_hit"],
                "forbidden_findings_hit": quality["forbidden_findings_hit"],
                "known_unresolved_preserved": quality["known_unresolved_preserved"],
                "known_unresolved_total": quality["known_unresolved_total"],
                "necessity": out["necessity"],
            }
        )
        if not ok:
            failures += 1
    return {
        "status": "pass" if failures == 0 else "fail",
        "cases": results,
        "expected_answers": "sealed — compared in-process, never echoed",
    }


def _safe_run_dir(runs_root: Path, run_name: str) -> Path:
    """Resolve ``runs_root / run_name`` refusing traversal and absolute
    paths — a run is a directory *inside* the runs root, never an escape.
    Belt-and-suspenders: the name must match a safe pattern AND the
    resolved path must stay under the root."""
    if not _SAFE_RUN_NAME.match(run_name or ""):
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: run name {run_name!r} invalido — "
            "use [A-Za-z0-9._-] sem separadores"
        )
    root = runs_root.resolve()
    run_dir = (root / run_name).resolve()
    if run_dir != root and root not in run_dir.parents:
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: run {run_name!r} fora de {root}"
        )
    return run_dir


def result(suite_id: str, run_name: str) -> dict[str, Any]:
    """evals.result — the scorecard of a recorded agentic run.

    Only meaningful for host-executed suites (the deterministic ones emit
    their result at run time). Reads the run dir under
    ``~/.sparkforge-azure/agentic-evals/<run>`` and grades it — the same
    computation as ``python -m sparkforge_azure.evals grade`` — but never
    echoes the sealed gabarito: the scorecard carries per-question
    pass/fail, not the expected answers."""
    s = taxonomy.get(suite_id)
    if not suite_id.startswith("agentic-"):
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: evals.result aplica-se a suites "
            "executadas por host (agentic-*); suites deterministicas emitem "
            "o resultado no proprio `evals run`"
        )
    from sparkforge_azure.evals.cli import (
        RUNS_ROOT,
        SCORECARD,
        EvalError,
        _suite_dir,
        eval_grade,
    )

    agentic_name = suite_id[len("agentic-"):]
    run_dir = _safe_run_dir(RUNS_ROOT, run_name)
    if not run_dir.is_dir():
        raise taxonomy.TaxonomyError(
            f"{taxonomy.E_UNAVAILABLE}: run {run_name!r} ausente em {RUNS_ROOT}; "
            "grave-o executando a suite num host"
        )
    scorecard_path = run_dir / SCORECARD
    if scorecard_path.is_file():
        payload = json.loads(scorecard_path.read_text(encoding="utf-8"))
    else:
        try:
            payload = eval_grade(_suite_dir(agentic_name), run_dir)
        except EvalError as exc:
            raise taxonomy.TaxonomyError(str(exc)) from exc
        scorecard_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return _envelope(s, status="ok", run=run_name, scorecard=payload)


__all__ = ["result", "run"]
