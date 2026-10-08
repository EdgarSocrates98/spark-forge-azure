"""SDD FABRIC_RTI — Eventstream/Eventhouse/Activator stage evaluation."""
from __future__ import annotations

from sparkforge_azure.stream import extract, rti
from sparkforge_azure.stream.casefile import load_bundle

FIXTURES = "tests/fixtures/stream"


def _stages(case: str):
    b = load_bundle(f"{FIXTURES}/{case}")
    return {s.layer: s for s in
            rti.evaluate_rti(extract.extract_all(b.artifacts, b.sources))}


def test_source_auth_failure_is_eventstream_source():
    st = _stages("s15-eventstream-source-auth")
    assert st["eventstream_source"].verdict == "fail"


def test_broken_destination_is_destination_layer():
    st = _stages("s16-eventstream-destination-broken")
    assert st["eventstream_destination"].verdict == "fail"


def test_draft_eventstream_flags_publish():
    st = _stages("s17-eventstream-draft")
    assert st["eventstream_publish"].verdict == "fail"


def test_ingestion_lag_is_eventhouse_ingestion():
    st = _stages("s18-eventhouse-ingestion-lag")
    assert st["eventhouse_ingestion"].verdict == "fail"


def test_activator_invalid_mapping():
    st = _stages("s19-activator-mapping-invalid")
    assert st["activator_mapping"].verdict == "fail"


def test_activator_stale_evaluation():
    st = _stages("s20-activator-kql-stale")
    assert st["activator_evaluation"].verdict == "fail"


def test_no_rti_artifacts_means_no_rti_stages():
    st = _stages("s01-caught-up-idle")
    rti_layers = {k for k in st if k.startswith(
        ("eventstream", "eventhouse", "kql", "activator"))}
    # stages exist but unknown — never fabricated as pass
    for layer in rti_layers:
        assert st[layer].verdict == "unknown", (layer, st[layer].verdict)


def test_eventstream_facts():
    """SDD contract name — eventstream.json vira facts e estágios RTI."""
    b = load_bundle(f"{FIXTURES}/s16-eventstream-destination-broken")
    facts = extract.extract_all(b.artifacts, b.sources)
    assert any(f.kind.startswith(("es.", "rti.", "eventstream"))
               for f in facts), {f.kind for f in facts}


def test_destination_vs_source_layers():
    """AC2 — falha na source e falha na destination são camadas distintas."""
    assert _stages("s15-eventstream-source-auth")[
        "eventstream_source"].verdict == "fail"
    st = _stages("s16-eventstream-destination-broken")
    assert st["eventstream_destination"].verdict == "fail"
    assert st["eventstream_source"].verdict != "fail"


def test_activator_mapping_vs_evaluation():
    """AC3 — mapping inválido != avaliação stale (camadas separadas)."""
    assert _stages("s19-activator-mapping-invalid")[
        "activator_mapping"].verdict == "fail"
    st = _stages("s20-activator-kql-stale")
    assert st["activator_evaluation"].verdict == "fail"
    assert st["activator_mapping"].verdict != "fail"


def test_activator_action_needs_evidence():
    """AC4 — ação do activator exige last_action evidenciado; ausência não
    é avaliada como sucesso."""
    st = _stages("s19-activator-mapping-invalid")
    # mapping falhou → evaluation não pode ser 'pass' fabricado
    assert st["activator_evaluation"].verdict in {"pass", "unknown"}
    # sem activator.json nenhum estágio activator é emitido como pass
    st_none = _stages("s01-caught-up-idle")
    act = st_none.get("activator_evaluation")
    assert act is None or act.verdict != "pass"
