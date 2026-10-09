"""SDD SKILLS_AGENTS_HARDENING — skills/agents só citam o que existe.

AC1-AC3: mirrors de agent declaram tools e "quando usar"; does_not é negação.
AC5-AC6: refs de CLI das skills resolvem para a CLI real e parseiam.
AC7: analyze-batch-loop ligado a um agent; ``scan`` genérico não vai ao purview.
"""
from __future__ import annotations

import json
import re
import shlex
import shutil
from pathlib import Path

import pytest

from sparkforge_azure.agentmanifest.mirrors import AGENT_MIRROR_ROOTS, mirror_name
from sparkforge_azure.agentmanifest.model import (
    load_manifests,
    validate_agents_tree,
)
from sparkforge_azure.agentmanifest.routing import ROUTING_TABLE, route
from sparkforge_azure.cli.main import build_parser, command_paths, main
from sparkforge_azure.skills.model import (
    CLI_NAME,
    body_cli_refs,
    discover_skill_files,
    parse_skill,
    split_front_matter,
)

REPO = Path(__file__).resolve().parents[1]
_NEGATION = re.compile(r"^(não|nao|nunca)\b", re.IGNORECASE)


def _mirror_front(agent_id: str) -> dict:
    path = REPO / ".claude" / "agents" / "custom" / f"{mirror_name(agent_id)}.md"
    _, data, _ = split_front_matter(path.read_text(encoding="utf-8"))
    return data


def _skills():
    return [parse_skill(p) for p in discover_skill_files(REPO)]


def _body_commands(body: str) -> list[str]:
    """Linhas ``sparkforge-azure ...`` dentro de blocos cercados do corpo."""
    out: list[str] = []
    for block in re.findall(r"```[a-z]*\n(.*?)```", body, re.S):
        for line in block.splitlines():
            line = line.split("#", 1)[0].strip()
            if line.startswith(f"{CLI_NAME} "):
                out.append(line)
    return out


# ---- AC1 / AC2 / AC3 — agents ------------------------------------------------


def test_ac1_mirror_declares_host_tools() -> None:
    for m in load_manifests(REPO):
        for mroot in AGENT_MIRROR_ROOTS:
            path = REPO / mroot / f"{mirror_name(m.id)}.md"
            _, data, _ = split_front_matter(path.read_text(encoding="utf-8"))
            tools = [t.strip() for t in str(data.get("tools", "")).split(",") if t.strip()]
            assert tools, f"{path}: mirror sem tools (host daria todas as tools)"
            assert not {"Write", "Edit", "NotebookEdit", "WebFetch", "Agent"} & set(tools)
            needs_cli = any(t.startswith("sfa_") for t in m.allowed_tools)
            assert ("Bash" in tools) == needs_cli, f"{m.id}: Bash só com tool sfa_*"


def test_ac2_mirror_description_says_when() -> None:
    for r in ROUTING_TABLE:
        desc = str(_mirror_front(r.specialist)["description"])
        assert "Use quando" in desc, r.specialist
        assert any(term in desc.lower() for term in r.terms), r.specialist
    descs = [str(_mirror_front(r.specialist)["description"]) for r in ROUTING_TABLE]
    assert len(set(descs)) == len(descs)


def test_ac3_does_not_is_negation(tmp_path: Path) -> None:
    for m in load_manifests(REPO):
        for item in m.list("does_not"):
            assert _NEGATION.match(item), f"{m.id}: does_not não é negação: {item!r}"
    # o validador recusa o contrário
    shutil.copytree(REPO / "agents", tmp_path / "agents")
    src = tmp_path / "agents" / "delta-specialist.md"
    text = src.read_text(encoding="utf-8")
    src.write_text(text.replace("does_not:\n", "does_not:\n- VACUUM é avaliado\n", 1),
                   encoding="utf-8")
    rep = validate_agents_tree(tmp_path, allow_pending_knowledge=True)
    assert any("does_not" in e and "negation" in e for e in rep.errors), rep.errors


# ---- AC5 / AC6 — skills ------------------------------------------------------


def _resolves(ref: str, paths: list[str]) -> bool:
    cmd = ref.removeprefix(f"{CLI_NAME} ").strip()
    return cmd in paths or any(p.startswith(cmd + " ") for p in paths)


def test_ac5_skill_cli_refs_resolve() -> None:
    paths = command_paths()
    for s in _skills():
        for ref in s.tool_refs:
            if ref.startswith(f"{CLI_NAME} "):
                assert _resolves(ref, paths), f"{s.name}: tool_ref sem comando: {ref}"
        for ref in body_cli_refs(s.body):
            assert _resolves(ref, paths), f"{s.name}: corpo cita comando inexistente: {ref}"
        for ref in s.meta_list("planned_tool_refs"):
            assert not _resolves(ref, paths), f"{s.name}: {ref} já existe, não é planned"
            assert ref not in s.body, f"{s.name}: verbo planejado no corpo: {ref}"


def test_ac5_validator_refuses_missing_command(tmp_path: Path) -> None:
    from sparkforge_azure.skills.model import validate_skills_tree

    shutil.copytree(REPO / "skills", tmp_path / "skills")
    p = tmp_path / "skills" / "azure-databricks" / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "  tool_refs:\n", "  tool_refs:\n  - sparkforge-azure analyze dab\n", 1),
        encoding="utf-8")
    rep = validate_skills_tree(tmp_path, allow_pending_knowledge=True)
    assert any("analyze dab" in e and "not a real CLI command" in e for e in rep.errors)


def _lab_slugs(capsys) -> set[str]:
    capsys.readouterr()
    main(["lab", "scenarios"])
    data = json.loads(capsys.readouterr().out)
    return {s["slug"] for s in data["scenarios"]} | {s["id"] for s in data["scenarios"]}


def test_ac6_skill_body_commands_parse(capsys) -> None:
    parser = build_parser()
    slugs = _lab_slugs(capsys)
    seen = 0
    for s in _skills():
        for line in _body_commands(s.body):
            argv = shlex.split(line)[1:]
            try:
                args = parser.parse_args(argv)
            except SystemExit:  # argparse recusa
                pytest.fail(f"{s.name}: CLI recusa `{line}`")
            seen += 1
            if argv[:2] == ["lab", "run"] and getattr(args, "scenario", None):
                assert args.scenario in slugs, f"{s.name}: cenário inexistente {args.scenario}"
    assert seen >= 22  # toda skill mostra ao menos um comando executável


# ---- AC7 — wiring --------------------------------------------------------------


def test_ac7_batch_loop_wired_and_scan_not_purview() -> None:
    used = {sk for m in load_manifests(REPO) for sk in m.list("skills")}
    assert "analyze-batch-loop" in used
    assert "purview-specialist" not in route("full table scan lento no job spark")
    assert "purview-specialist" in route("o purview scan do data map falhou")
