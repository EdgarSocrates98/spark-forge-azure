"""SDD SYNAPSE_FABRIC_SPARK — refactor patterns detected with file:line,
config classification, library unknowns are REVIEW, notebook dep graph."""
from __future__ import annotations

from sparkforge_azure.migration import extract, spark

NOTEBOOK_SRC = """\
# nb_main
df = spark.read.synapsesql("sql.pool.table")
token = mssparkutils.credentials.getToken("storage")
ls_props = mssparkutils.credentials.getPropertiesAsMap("ls_kv")
mssparkutils.notebook.run("nb_child")
path = "/user/trusted-service-user/foo/bar"
spark.catalog.listFunctions()
"""


def _nb_fact(name="nb_main"):
    estate = {"synapse_workspaces": [{
        "id": "syn-1", "name": "s1",
        "notebooks": [{"id": f"syn-1/nb/{name}", "name": name,
                       "path": f"notebooks/{name}.py"}]}]}
    return extract.extract_all({"estate": estate},
                               {"estate": "estate.json"})


def test_refactor_patterns_detected():
    """AC1: official patterns -> typed findings with file:line evidence."""
    findings = spark.scan_notebook_source(NOTEBOOK_SRC,
                                          "notebooks/nb_main.py")
    pats = {f["pattern"] for f in findings}
    assert "synapsesql" in pats
    assert "mssparkutils" in pats
    assert "getPropertiesAsMap" in pats
    assert "/user/trusted-service-user/" in pats
    assert "spark.catalog.listFunctions" in pats
    unsupported = [f for f in findings if f["status"] == "unsupported"]
    assert unsupported and unsupported[0]["line"] == 7
    assert all(f["file"] == "notebooks/nb_main.py" for f in findings)


def test_spark_config_classified():
    """AC2: configs are classified — supported / not_migratable /
    unknown; never silently carried."""
    assert spark.classify_spark_config(
        "spark.sql.shuffle.partitions") == "supported"
    assert spark.classify_spark_config(
        "spark.synapse.linkedService") == "not_migratable"
    assert spark.classify_spark_config(
        "spark.vendor.custom") == "unknown"


def test_library_unknown_is_review():
    """AC3: library without proven Fabric compatibility -> UNRESOLVED /
    unknown, never 'unsupported' or 'compatible' by default."""
    libs = extract.extract_all(
        {"estate": {"synapse_workspaces": [{
            "id": "syn-1", "name": "s1",
            "libraries": [{"name": "vendor-wheel", "kind": "whl",
                           "version": "9.9"}]}]}},
        {"estate": "estate.json"})
    out = spark.assess_libraries(libs)
    assert out[0]["status"] == "unknown"
    assert out[0]["readiness"] == "UNRESOLVED"
    out2 = spark.assess_libraries(libs, known_fabric={"vendor-wheel"})
    assert out2[0]["status"] == "compatible"
    assert out2[0]["readiness"] == "READY"


def test_notebook_dependency_graph():
    """AC4: %run / notebook.run edges between notebooks (blast radius)."""
    nbs = [{"name": "nb_main", "path": "notebooks/nb_main.py"},
           {"name": "nb_child", "path": "notebooks/nb_child.py"}]
    sources = {"notebooks/nb_main.py": NOTEBOOK_SRC,
               "notebooks/nb_child.py": "print('leaf')"}
    g = spark.notebook_dependency_graph(nbs, sources)
    assert g["edge_count"] == 1
    assert g["edges"][0]["src"] == "nb_main"
    assert g["edges"][0]["dst"] == "nb_child"
    assert g["edges"][0]["relation"] == "invokes"


def test_notebook_readiness_worst_of():
    nb = _nb_fact()
    nbf = next(f for f in nb if f.kind == "mig.synapse_notebook")
    out = spark.assess_notebook(nbf, NOTEBOOK_SRC, "notebooks/nb_main.py")
    assert out["readiness"] == "BLOCKED"  # listFunctions is unsupported
    clean = spark.assess_notebook(nbf, "print(1)", "notebooks/ok.py")
    assert clean["readiness"] == "READY"
    missing = spark.assess_notebook(nbf, None, "notebooks/x.py")
    assert missing["readiness"] == "UNRESOLVED"
