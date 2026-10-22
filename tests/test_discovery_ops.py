"""lf-0037: §6.2 discovery ops —  op 、、。

:
- discovery_ops （8 ops ->  command id ->  CLI）
- rules search/get（query/category/severity//get ）
- knowledge search/get/list（sha256、provenance、domain、、）
- context pack（forge/context-pack/v1、、 hash）
- capabilities（ + ops ）
- manifest discovery.commands/ops 
- skill  knowledge  stub（）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_ops_map_covers_all_eight_conceptual_ops():
    from sparkforge_azure import discovery_ops

    expected = {
        "capabilities.list",
        "protocol.describe",
        "rules.search",
        "rules.get",
        "knowledge.search",
        "knowledge.get",
        "context.build",
        "health.check",
    }
    assert set(discovery_ops.ops()) == expected


def test_op_command_ids_registered_in_cli(tmp_path=None):
    """ ops  command id  argv  CLI 。"""
    from sparkforge_azure import discovery_ops
    from sparkforge_azure.cli.main import build_parser

    parser = build_parser()
    top = next(
        a for a in parser._actions if isinstance(a, __import__("argparse")._SubParsersAction)
    )
    for op, entry in discovery_ops.OPS.items():
        argv = entry["argv"]
        head = argv[0]
        assert head in top.choices, f"{op} -> {head} "
        # （）
        if len(argv) > 1 and not argv[1].startswith("{"):
            leaf = next(
                a
                for a in top.choices[head]._actions
                if isinstance(a, __import__("argparse")._SubParsersAction)
            )
            leaf_name = argv[1]
            assert leaf_name in leaf.choices, f"{op} -> {head} {leaf_name} "


def test_commands_ids_unique_and_match_ops():
    from sparkforge_azure import discovery_ops

    cmds = discovery_ops.commands()
    ids = [c["id"] for c in cmds]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(discovery_ops.ops().values())
    for c in cmds:
        assert c["argv"][0] == discovery_ops.CLI
        assert c["read_only"] is True


def test_rules_search_filters_and_pagination():
    from sparkforge_azure import discovery

    page1 = discovery.rules_search(query="fabric", limit=2)
    assert page1["status"] == "ok"
    assert page1["total"] >= 2
    assert len(page1["rules"]) == 2
    assert page1["next_cursor"] == "2"
    page2 = discovery.rules_search(query="fabric", limit=2, cursor=page1["next_cursor"])
    ids1 = {r["id"] for r in page1["rules"]}
    ids2 = {r["id"] for r in page2["rules"]}
    assert not ids1 & ids2
    assert page1["filters_applied"]["query"] == "fabric"


def test_rules_search_severity_and_index_mode():
    from sparkforge_azure import discovery

    out = discovery.rules_search(severity="P1", index=True, limit=5)
    for r in out["rules"]:
        assert r["severity_default"] == "P1"
        assert set(r) <= set(discovery.INDEX_FIELDS) | {"source_file"}


def test_rules_get_found_and_missing():
    from sparkforge_azure import discovery

    out = discovery.rules_get("SF-FAB-001")
    assert out["found"] is True and out["rule"]["id"] == "SF-FAB-001"
    missing = discovery.rules_get("SF-NOPE-999")
    assert missing["found"] is False and missing["rule"] is None


def test_knowledge_search_one_hit_per_doc_with_sha256():
    from sparkforge_azure import discovery

    out = discovery.knowledge_search("fabric", limit=2)
    assert out["documents_total"] >= 2
    assert len(out["documents"]) == 2
    assert out["next_cursor"] == "2"
    for doc in out["documents"]:
        assert doc["ref"].endswith(".md")
        assert len(doc["sha256"]) == 64
        assert doc["matched_lines"] >= 1
        assert len(doc["snippets"]) <= 3
    assert out["knowledge_origin"] in ("checkout", "package", "env")


def test_knowledge_search_domain_filter():
    from sparkforge_azure import discovery

    out = discovery.knowledge_search("spark", domain="microsoft-fabric")
    for doc in out["documents"]:
        seg = doc["ref"].lower()
        assert "fabric" in seg, seg


def test_knowledge_get_provenance_and_escape_guard():
    import pytest

    from sparkforge_azure import discovery
    from sparkforge_azure.knowledge_ref import KnowledgeError

    out = discovery.knowledge_get("INDEX.md")
    doc = out["document"]
    assert doc["ref"] == "INDEX.md"
    assert Path(doc["path"]).is_file()
    assert len(doc["sha256"]) == 64
    assert doc["bytes"] > 0
    with pytest.raises(KnowledgeError):
        discovery.knowledge_get("../pyproject.toml")


def test_capabilities_real_counts_and_ops():
    from sparkforge_azure import discovery, discovery_ops

    caps = discovery.capabilities()
    assert caps["offline"] is True
    assert caps["rules"]["count"] > 0
    assert caps["knowledge"]["documents"] > 0
    assert set(caps["operations"]) == set(discovery_ops.ops())
    for op, spec in caps["operations"].items():
        assert spec["command"] == discovery_ops.ops()[op]


def test_context_pack_bounded_deterministic():
    from sparkforge_azure import discovery

    p1 = discovery.context_pack("microsoft-fabric", rules_limit=5, knowledge_limit=3)
    p2 = discovery.context_pack("microsoft-fabric", rules_limit=5, knowledge_limit=3)
    assert p1["schema"] == "forge/context-pack/v1"
    assert p1["pack_sha256"] == p2["pack_sha256"]
    assert len(p1["rules"]) <= 5
    assert len(p1["knowledge"]["documents"]) <= 3
    for doc in p1["knowledge"]["documents"]:
        assert len(doc["sha256"]) == 64
        assert "text" not in doc and "body" not in doc  #  dump 
    assert p1["operations"]["context.build"] == "context-pack"


def test_context_pack_domain_filters_rules():
    from sparkforge_azure import discovery

    fabric = discovery.context_pack("microsoft-fabric")
    for r in fabric["rules"]:
        hay = f"{r['id']} {r['category'] or ''} {r['title'] or ''}".lower()
        assert "fab" in hay or "fabric" in hay


def test_manifest_ops_and_commands_consistent():
    from sparkforge_azure import discovery_ops
    from sparkforge_azure.install.service import _context_manifest

    m = _context_manifest(
        scope="project", profile="recommended", hosts=["claude"], components=None
    )
    ops = m["discovery"]["ops"]
    assert set(ops) == set(discovery_ops.ops())
    ids = {c["id"] for c in m["discovery"]["commands"]}
    assert set(ops.values()) <= ids


def test_knowledge_pointer_stubs_for_skill_refs(tmp_path):
    """， SKILL.md  knowledge/<rel>  stub。"""
    from sparkforge_azure.install import service

    ledger = {"version": 1, "files": []}
    ledger, written = service._install_skill_mirrors(tmp_path, ledger, ("claude",))
    stubs = [w for w in written if "/knowledge/" in w]
    assert stubs, "expected knowledge pointer stubs"
    for stub in stubs:
        body = Path(stub).read_text(encoding="utf-8")
        assert "PONTEIRO" in body
        assert "sparkforge-azure knowledge" in body
    # stub  ledger（uninstall ）
    kinds = {f["kind"] for f in ledger["files"]}
    assert "knowledge_pointer" in kinds
