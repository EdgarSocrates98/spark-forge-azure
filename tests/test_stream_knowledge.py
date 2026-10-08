"""SDD STREAMING_ECONOMY_OBSERVABILITY — knowledge pack scoping (stream)."""
from __future__ import annotations

from sparkforge_azure.knowledgebase.vertical import (
    compile_access_knowledge,
    load_packs,
    packs_for_layer,
)


def test_stream_packs_registered():
    packs = load_packs()["packs"]
    for name in ("eventhubs-core", "spark-structured-streaming",
                 "stream-correctness", "fabric-rti", "stream-economy"):
        assert name in packs, name
        assert packs[name]["vertical"] == "stream"


def test_stream_layer_scoping():
    assert "eventhubs-core" in packs_for_layer(
        "event_hubs_capacity", vertical="stream")
    assert packs_for_layer("checkpoint", vertical="stream") == [
        "spark-structured-streaming"]
    assert "fabric-rti" in packs_for_layer(
        "activator_evaluation", vertical="stream")


def test_stream_case_never_loads_other_verticals():
    k = compile_access_knowledge("checkpoint", "streaming query lag",
                               vertical="stream")
    assert "spark-structured-streaming" in k["packs"]
    for foreign in ("unity-catalog-storage", "onelake-security",
                    "fabric-spark"):
        assert foreign not in k["packs"]


def test_unresolved_stream_case_stays_in_vertical():
    k = compile_access_knowledge("unresolved", "stream case",
                               vertical="stream")
    for pack in k["packs"]:
        spec = load_packs()["packs"][pack]
        assert spec["vertical"] == "stream", pack


def test_cross_vertical_layer_names_resolve_to_caller():
    """`cross_environment` exists in access/fabric/stream — scoping must
    resolve to the caller's vertical only."""
    assert packs_for_layer("cross_environment", vertical="stream") == [
        "eventhubs-core"]
    assert packs_for_layer("cross_environment", vertical="access") == [
        "azure-identity"]
