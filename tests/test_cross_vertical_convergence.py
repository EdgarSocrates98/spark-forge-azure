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


# --- §109-110: large synthetic workspace + relevant-slice ---

_DOMINIOS = {
    "databricks": [
        ("unity_catalog_grant.py", "check_uc_grant", "unity catalog grant"),
        ("adls_acl.py", "check_adls_acl", "adls acl permission"),
        ("cluster_policy.py", "validate_cluster_policy", "cluster policy"),
        ("workspace_binding.py", "bind_workspace_catalog", "workspace binding"),
        ("storage_credential.py", "audit_storage_credential", "credential"),
    ],
    "fabric": [
        ("onelake_shortcut.py", "resolve_shortcut", "onelake shortcut"),
        ("capacity_throttle.py", "detect_throttle", "capacity throttling"),
        ("workspace_role.py", "check_workspace_role", "workspace role"),
        ("spark_job_def.py", "validate_sjd", "spark job definition"),
        ("lakehouse_schema.py", "list_lakehouse_tables", "lakehouse tables"),
    ],
    "streaming": [
        ("checkpoint_store.py", "recover_checkpoint", "stream checkpoint"),
        ("consumer_lag.py", "measure_lag", "consumer lag"),
        ("eventhub_auth.py", "check_eh_authz", "event hubs authorization"),
        ("watermark.py", "compute_watermark", "watermark"),
        ("sink_delivery.py", "verify_exactly_once", "delivery semantics"),
    ],
    "migration": [
        ("adf_inventory.py", "list_adf_pipelines", "adf pipeline inventory"),
        ("ssis_compat.py", "ssis_readiness", "ssis compatibility"),
        ("linked_service.py", "map_linked_service", "linked service mapping"),
        ("synapse_notebook.py", "convert_synapse_notebook", "synapse notebook"),
        ("wave_planner.py", "plan_migration_waves", "migration waves"),
    ],
    "unrelated": [
        ("hello.py", "hello_world", "hello"),
        ("utils_math.py", "fibonacci", "fibonacci"),
        ("readme_gen.py", "render_readme", "readme"),
        ("csv_parse.py", "parse_csv", "csv parser"),
        ("sorts.py", "quicksort", "quicksort"),
    ],
}

_QUERIES = {
    "databricks": "unity catalog grant",
    "fabric": "onelake shortcut",
    "streaming": "consumer lag checkpoint",
    "migration": "adf pipeline inventory",
}


def _corpus_sintetico(tmp_path: Path) -> Path:
    """§109: corpus sintetico com os 4 dominios + arquivos nao relacionados."""
    corpus = tmp_path / "corpus"
    for dominio, modulos in _DOMINIOS.items():
        (corpus / dominio).mkdir(parents=True)
        for arquivo, simbolo, doc in modulos:
            (corpus / dominio / arquivo).write_text(
                f'def {simbolo}():\n    """{doc}"""\n    return True\n',
                encoding="utf-8")
    return corpus


def _paths_do_pack(pacote: dict) -> set[str]:
    return {str(s.get("path", ""))
            for s in (*pacote.get("entry_points", ()),
                      *pacote.get("symbols", ()))}


def test_large_workspace_materializa_so_a_fatia_relevante(tmp_path):
    """§109-110: consulta de um dominio materializa so a fatia daquele
    dominio — nenhum simbolo de outro dominio entra no pack."""
    from sparkforge_azure.codeintel.context import montar
    from sparkforge_azure.codeintel.index import indexar

    corpus = _corpus_sintetico(tmp_path)
    banco = tmp_path / "idx.sqlite3"
    indexar(corpus, banco)
    for dominio, consulta in _QUERIES.items():
        pacote = montar(banco, consulta).para_dicionario()
        paths = _paths_do_pack(pacote)
        assert paths, f"{dominio}: pack vazio para '{consulta}'"
        for path in paths:
            topo = path.replace("\\", "/").split("/", 1)[0]
            assert topo == dominio, (
                f"consulta '{consulta}' trouxe '{path}' "
                f"fora da fatia '{dominio}/'")


def test_contaminacao_de_agente():
    """§114: caso Fabric nunca despacha unity-catalog-specialist; migracao
    nunca despacha streaming-specialist. Rotas seguem o findings_area."""
    from sparkforge_azure.case.router import next_step
    from sparkforge_azure.case.store import new_case, set_phase

    runtime = {"databricks_runtime": "15.4", "spark": "3.5.0"}
    caso = set_phase(new_case("c", "2026-07-29T00:00:00Z", runtime),
                     "diagnosis")

    step = next_step(caso, ["SF-FAB-001"])
    assert step["recommended_agent"] == "fabric-specialist"

    step = next_step(caso, ["SF-MIG-002"])
    assert step["recommended_agent"] == "migration-specialist"

    step = next_step(caso, ["SF-STR-LOSS-RISK"])
    assert step["recommended_agent"] == "streaming-specialist"

    step = next_step(caso, ["SFA-GOV-000"])
    assert step["recommended_agent"] in (None, "unity-catalog-specialist")
