"""Convergence lab gate (prompt_evo_cycle6 §19-20, §106-114).

Valida que os quatro verticais (databricks/fabric/stream/migration)
compartilham o mesmo contrato de resultado e que nao ha contaminacao
cruzada de dominio, grafo, memoria ou agente.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals" / "convergence"))

from runner import PIPELINES, run_suite  # noqa: E402

FIXTURES = {
    "databricks": ROOT / "tests/fixtures/access/s01_uc_privilege_denied",
    "fabric": ROOT / "tests/fixtures/fabric/f05_shortcut_target_missing",
    "stream": ROOT / "tests/fixtures/stream/s08-checkpoint-deleted-latest",
    "migration": ROOT / "tests/fixtures/migration/m02-ssis-blocked",
}

_GRAPH_KEYS = {"databricks": "access_graph", "fabric": "fabric_graph",
               "stream": "stream_graph", "migration": "migration_graph"}


def test_lab_all_cells_pass():
    """§19: um caso por vertical x todos os profiles — zero violacoes."""
    report = run_suite()
    assert report["ok"], report["violacoes"]
    assert report["cells"] == 4 * 5


def test_environment_fingerprint_deterministico():
    """Mesmo caso -> mesmo fingerprint; eixo diferente -> fingerprint muda."""
    r1 = PIPELINES["databricks"](FIXTURES["databricks"])
    r2 = PIPELINES["databricks"](FIXTURES["databricks"])
    fp1 = r1["case_meta"]["environment_fingerprint"]
    fp2 = r2["case_meta"]["environment_fingerprint"]
    assert fp1 == fp2
    assert fp1["axes"]["workspace_id"] == "1234567890123456"


def test_resultado_e_json_serializavel():
    for vertical, fixture in FIXTURES.items():
        result = PIPELINES[vertical](fixture)
        json.dumps(result)  # nao pode levantar


def test_contaminacao_cruzada_de_dominio():
    """Facts de um vertical nao vazam para o resultado de outro."""
    estrangeiros = {
        "databricks": ("mig.", "fabric.", "onelake.", "eh.", "stream.",
                       "consumer."),
        "fabric": ("mig.", "unity_catalog.", "adls.", "eh.", "stream.",
                   "consumer."),
        "stream": ("mig.", "unity_catalog.", "adls.", "fabric.", "onelake."),
        "migration": ("unity_catalog.", "adls.", "onelake.", "eh.", "stream.",
                      "consumer."),
    }
    for vertical, fixture in FIXTURES.items():
        result = PIPELINES[vertical](fixture)
        for fact in result["facts"]:
            assert not fact["kind"].startswith(estrangeiros[vertical]), (
                f"{vertical}: kind estrangeiro {fact['kind']}")


def test_contaminacao_de_grafo():
    """Nos do grafo de um vertical nao carregam ids de dominio estrangeiro."""
    marcadores = {
        "databricks": ("onelake", "adf-1", "eventhub"),
        "fabric": ("unity_catalog", "adf-1", "eventhub"),
        "stream": ("unity_catalog", "onelake", "adf-1"),
        "migration": ("onelake", "eventhub", "unity_catalog"),
    }
    for vertical, fixture in FIXTURES.items():
        result = PIPELINES[vertical](fixture)
        grafo = result[_GRAPH_KEYS[vertical]]
        ids = json.dumps(grafo["nodes"])
        for marcador in marcadores[vertical]:
            assert marcador not in ids, (
                f"{vertical}: grafo contaminado por '{marcador}'")


def test_contaminacao_de_memoria(tmp_path):
    """Fingerprint de ambiente diferente => registro de outro ambiente
    nao ganha o match ambiental (§113)."""
    from sparkforge_azure.agentic.memory import (
        DECISIONS_FILE,
        memory_path,
        retrieve_memory,
    )

    def gravar(records):
        path = memory_path(tmp_path)
        path.mkdir(parents=True, exist_ok=True)
        with (path / DECISIONS_FILE).open("a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, sort_keys=True) + "\n")

    base = {
        "problem": "workspace notebook cannot reach storage",
        "problem_fingerprint": "",
        "status": "accepted",
        "decision": "fix",
        "decision_evidence": ["f1"],
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    gravar([
        {**base, "id": "env-a", "environment_fingerprint": "fp-a",
         "runtime": {"spark": "3.5"}},
        {**base, "id": "env-b", "environment_fingerprint": "fp-b",
         "runtime": {"spark": "3.5"}},
    ])
    hits = retrieve_memory("workspace notebook cannot reach storage",
                           tmp_path, environment_fingerprint="fp-b")
    assert hits, "nenhum registro retornado"
    por_id = {h["id"]: h for h in hits}
    # o registro do ambiente B pontua ambiente; o de A nao
    assert (por_id["env-b"]["retrieval"]["environment"]
            > por_id["env-a"]["retrieval"]["environment"])


def test_trust_nunca_elevado_nos_quatro_verticais():
    """§20: DATA_ONLY nunca escala silenciosamente — confianca sempre
    EXTERNAL_DATA + data_only."""
    for vertical, fixture in FIXTURES.items():
        result = PIPELINES[vertical](fixture)
        trust = result["trust"]
        assert trust["instruction_authority"] == "data_only"
        assert trust["taint"] == "external"
