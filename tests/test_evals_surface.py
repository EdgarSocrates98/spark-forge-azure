"""`sparkforge-azure evals` + a classificacao §7.1 persistida no manifesto
forge/context/v1 (lf-0038, install-2.0 ciclo 5).

O que este arquivo prova, na ordem:

1. as 4 categorias do §7.1 existem e toda suite declarada carrega uma;
2. o manifesto registra a classificacao (`eval_suites[].kind` +
   `capabilities.evals.detail`) dentro do shape fechado (id, kind, command);
3. §7.3 — gabaritos selados nunca saem: nem `describe`, nem `list`, nem o
   manifesto ecoam conteudo de `expected/` ou de qualquer resposta; suites
   de host recusam execucao pela CLI (executor != avaliador); e toda suite
   declara o ambiente que a prova representa (deterministico != real);
4. os runners deterministicos rodam e marcam o ambiente no resultado.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from sparkforge_azure import discovery_ops
from sparkforge_azure.evals import surface, taxonomy
from sparkforge_azure.install.service import _context_manifest

ROOT = Path(__file__).resolve().parents[1]
CLI = "sparkforge-azure"

_ITEM_ID_RE = re.compile(r"^[a-z0-9-_]{1,128}$")


# ---------------------------------------------------------------------------
# §7.1 — a classificacao existe, e completa
# ---------------------------------------------------------------------------


def test_all_suites_carry_a_declared_kind():
    kinds = set(taxonomy.KINDS)
    for suite in taxonomy.catalog():
        assert suite["kind"] in kinds, suite["id"]
        assert suite["environment"] in ("deterministic", "host")
        assert _ITEM_ID_RE.match(suite["id"]), f"id fora do ITEM_ID_RE: {suite['id']}"


def test_the_four_categories_are_all_populated():
    counts = taxonomy.kind_counts()
    assert set(counts) == {
        "developer",
        "runtime-decision",
        "output-verification",
        "host-conformance",
    }
    assert all(v > 0 for v in counts.values()), counts


def test_listing_is_the_classified_inventory():
    payload = taxonomy.listing()
    assert payload["counts"] == taxonomy.kind_counts()
    assert {s["id"] for s in payload["suites"]} == set(taxonomy.suite_ids())
    for suite in payload["suites"]:
        # o que o inventario NAO traz: conteudo de gabarito, resposta, expected
        assert "answer" not in suite
        assert "expected" not in suite


# ---------------------------------------------------------------------------
# manifesto forge/context/v1 — classificacao persistida, schema fechado
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def manifest():
    return _context_manifest(
        scope="project", profile="recommended", hosts=["claude"], components=None
    )


def test_manifest_eval_suites_are_classified(manifest):
    from sparkforge_azure import _forgecontext as fctx

    assert fctx.validate_manifest(manifest) == []
    suites = manifest["eval_suites"]
    assert {s["id"] for s in suites} == set(taxonomy.suite_ids())
    kinds = {s["kind"] for s in suites}
    assert kinds == set(taxonomy.KINDS), kinds
    for s in suites:
        assert s["kind"] in fctx.EVAL_KINDS
        # shape fechado (id, kind, command) — o command e o describe read-only
        assert set(s) == {"id", "kind", "command"}
        assert s["command"][:3] == [CLI, "evals", "describe"]


def test_manifest_evals_capability_detail(manifest):
    detail = manifest["capabilities"]["evals"]["detail"]
    for kind in taxonomy.KINDS:
        assert kind in detail


def test_manifest_declares_the_7_2_ops_as_commands(manifest):
    ids = {c["id"] for c in manifest["discovery"]["commands"]}
    for esperado in (
        "evals-list",
        "evals-describe",
        "evals-run",
        "evals-result",
        "verification-plan",
        "verification-run",
    ):
        assert esperado in ids
    # e o mapa de ops do §6.2 continua fechado — nenhum op §7.2 nele
    assert not any(
        op.startswith(("evals.", "verification.")) for op in manifest["discovery"]["ops"]
    )


def test_eval_commands_source_is_discovery_ops():
    comandos = discovery_ops.eval_commands()
    assert [c["id"] for c in comandos] == [
        "evals-list",
        "evals-describe",
        "evals-run",
        "evals-result",
        "verification-plan",
        "verification-run",
    ]
    for c in comandos:
        assert c["argv"][0] == CLI
        assert _ITEM_ID_RE.match(c["id"])
    assert set(discovery_ops.eval_ops_expanded()) == {
        "evals.list",
        "evals.describe",
        "evals.run",
        "evals.result",
        "verification.plan",
        "verification.run",
    }


def test_capabilities_verb_reports_the_classification():
    from sparkforge_azure import discovery

    caps = discovery.capabilities()
    assert caps["eval_suites"] == taxonomy.suite_ids()
    assert caps["evals"]["counts"] == taxonomy.kind_counts()
    assert set(caps["evals"]["ops"]) == set(discovery_ops.eval_ops_expanded())


# ---------------------------------------------------------------------------
# §7.3 — gabarito selado, executor != avaliador, deterministico != real
# ---------------------------------------------------------------------------


def _fatias_de_resposta() -> list[str]:
    """Fatias de 40 chars do meio de cada arquivo de resposta conhecida — se
    qualquer uma aparecer num payload de describe/list/manifest, houve
    vazamento de gabarito (colisao de 40 chars e improvavel ao ponto de nao
    ser argumento)."""
    alvos = [
        *sorted((ROOT / "evals" / "agent_runtime" / "expected").glob("*.yaml")),
        *sorted((ROOT / "evals" / "agentic" / "sdd" / "baselines").rglob("*")),
    ]
    fatias: list[str] = []
    for arquivo in alvos:
        if not arquivo.is_file():
            continue
        texto = arquivo.read_text(encoding="utf-8")
        meio = len(texto) // 2
        fatias.append(texto[meio : meio + 40])
    assert len(fatias) >= 3
    return fatias


def test_describe_never_echoes_sealed_answers():
    """§7.3: o teste de exposicao — um agente pedindo `evals describe` de uma
    suite selada recebe metadados e hash, nunca bytes do gabarito."""
    for suite_id in taxonomy.suite_ids():
        payload = json.dumps(taxonomy.describe(suite_id), ensure_ascii=False)
        for fatia in _fatias_de_resposta():
            assert fatia not in payload, f"describe({suite_id}) vazou gabarito"


def test_listing_and_manifest_do_not_leak_answers(manifest):
    for payload in (
        json.dumps(taxonomy.listing(), ensure_ascii=False),
        json.dumps(manifest["eval_suites"], ensure_ascii=False),
        json.dumps(manifest["capabilities"]["evals"], ensure_ascii=False),
    ):
        for fatia in _fatias_de_resposta():
            assert fatia not in payload


def test_sealed_suites_mark_the_answers_as_not_emitted():
    seladas = [s for s in taxonomy.catalog() if s["sealed"]]
    assert seladas, "nenhuma suite selada — a postura §7.3 estaria vazia"
    for s in seladas:
        desc = taxonomy.describe(s["id"])
        assert desc["expected_answers"].startswith("sealed")
        assert desc["integrity"]["suite_sha256"] != "unresolved"


def test_evals_run_refuses_suites_that_only_a_host_executes():
    """§7.3: a CLI nao incorpora o agente avaliado — suites de host sao
    recusa nomeada, nao execucao sintetica."""
    for s in taxonomy.catalog():
        if s["environment"] != "host":
            continue
        with pytest.raises(taxonomy.TaxonomyError, match=taxonomy.E_HOST):
            surface.run(s["id"])


def test_evals_run_corpus_suite_is_unavailable_not_a_fake_pass():
    """§7.3: `parity` e corpus/baseline — `run` e recusa nomeada, nunca um
    veredito sintetico."""
    with pytest.raises(taxonomy.TaxonomyError, match=taxonomy.E_UNAVAILABLE):
        surface.run("parity")


def test_evals_result_rejects_non_host_suites():
    with pytest.raises(taxonomy.TaxonomyError, match=taxonomy.E_UNAVAILABLE):
        surface.result("convergence", "qualquer")


def test_unknown_suite_is_a_named_refusal():
    with pytest.raises(taxonomy.TaxonomyError, match=taxonomy.E_SUITE):
        taxonomy.describe("suite-inexistente")


def test_every_suite_marks_the_environment_it_proves():
    """§7.3: deterministico nao e prova de ambiente real — marcado em todo
    describe."""
    for s in taxonomy.catalog():
        desc = taxonomy.describe(s["id"])
        if s["environment"] == "host":
            assert "real environment" in desc["proof"]
        else:
            assert "not real-environment proof" in desc["proof"]


# ---------------------------------------------------------------------------
# runners deterministicos — evidencia real, falhas explicitas
# ---------------------------------------------------------------------------


def test_evals_run_mcp_conformance_marks_deterministic():
    payload = surface.run("mcp-conformance")
    assert payload["status"] == "pass"
    assert payload["environment"] == "deterministic"
    assert payload["real_environment_proof"] is False


def test_evals_run_agent_runtime_recomputes_cases():
    payload = surface.run("agent-runtime")
    assert payload["status"] == "pass"
    assert payload["environment"] == "deterministic"
    assert payload["real_environment_proof"] is False
    assert len(payload["cases"]) >= 4
    # o resultado nunca ecoa o arquivo expected — so o veredito do motor
    for fatia in _fatias_de_resposta():
        assert fatia not in json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI de verdade — os verbos existem e respondem
# ---------------------------------------------------------------------------


def _cli(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sparkforge_azure.cli.main", *argv],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def test_cli_evals_list():
    proc = _cli("evals", "list")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["counts"] == taxonomy.kind_counts()


def test_cli_evals_describe_agent_runtime_is_metadata_only():
    proc = _cli("evals", "describe", "--suite", "agent-runtime")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["sealed"] is True
    for fatia in _fatias_de_resposta()[:2]:
        assert fatia not in proc.stdout


def test_cli_evals_run_host_suite_refuses():
    proc = _cli("evals", "run", "--suite", "agentic-sdd")
    assert proc.returncode == 2
    assert "EVALS-REQUIRES-HOST" in proc.stdout


def test_cli_verification_ops_exist():
    """§7.4: verification.plan/run sao os verbos `lab plan`/`lab verify` —
    o fluxo plan->run->evidence e invocavel pela CLI, com falhas
    explicitas."""
    plan = _cli("lab", "plan", "--help")
    assert plan.returncode == 0
    verify = _cli("lab", "verify", "--help")
    assert verify.returncode == 0
