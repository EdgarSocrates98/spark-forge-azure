"""W4 — context resolution (prompt_evo_portable.md §48–§64).

`context resolve` answers "which context of this workspace is relevant to
this target" via the *declared* graph: reachable() picks the project set,
TokenSave walks the L0→L6 ladder per project confined to its own root, and
the §58 receipt records considered/selected, files, bytes and stop reason.
A project never receives another project's files without a declared edge
or explicit `all` (§64).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sparkforge_azure.distribution import workspace as ws_mod
from sparkforge_azure.distribution.context import context_resolve
from sparkforge_azure.distribution.errors import PortableError


def _make(tmp_path: Path) -> dict[str, str]:
    """ws/app -> lib, plus an undeclared sibling that must never leak."""
    ws = tmp_path / "ws"
    app = ws / "app"
    lib = tmp_path / "lib"
    stray = tmp_path / "stray"
    app.mkdir(parents=True)
    lib.mkdir()
    stray.mkdir()
    (app / "main.py").write_text("from lib import go\n", encoding="utf-8")
    (lib / "lib.py").write_text("def go():\n    return 1\n", encoding="utf-8")
    (stray / "secret.py").write_text("SECRET = 'x'\n", encoding="utf-8")
    ws_mod.workspace_init(ws)
    ws_mod.workspace_add(ws, "app", role="application")
    ws_mod.workspace_add(ws, str(lib), role="shared")
    data = ws_mod.workspace_status(ws)
    ids = {Path(p["resolved_path"]).name: p["id"] for p in data["projects"]}
    ws_mod.workspace_add(ws, "app", depends_on=(ids["lib"],))
    return {"ws": str(ws), "app": ids["app"], "lib": ids["lib"]}


def test_target_scope_only_reads_target(tmp_path: Path) -> None:
    ids = _make(tmp_path)
    out = context_resolve(Path(ids["ws"]), target=ids["app"], scope="target")
    assert out["projects_selected"] == [ids["app"]]
    # host + app + lib declared; stray/undeclared never considered
    assert len(out["projects_considered"]) == 3
    assert ids["app"] in out["projects_considered"]
    assert out["files_materialized"] == 0  # no task -> project set only
    assert out["stop_reason"] == "scope_complete"


def test_direct_scope_adds_declared_edges(tmp_path: Path) -> None:
    ids = _make(tmp_path)
    out = context_resolve(Path(ids["ws"]), target=ids["app"], scope="direct")
    assert set(out["projects_selected"]) == {ids["app"], ids["lib"]}


def test_all_scope_is_explicit(tmp_path: Path) -> None:
    ids = _make(tmp_path)
    out = context_resolve(Path(ids["ws"]), target=ids["app"], scope="all")
    assert len(out["projects_selected"]) == 3  # host + app + lib
    # undeclared sibling is never in the set (§64)
    assert "stray" not in " ".join(p["root"] for p in out["projects"])


def test_task_engages_ladder_with_bytes_accounting(tmp_path: Path) -> None:
    ids = _make(tmp_path)
    out = context_resolve(
        Path(ids["ws"]), target=ids["app"], scope="direct", task="def go lib"
    )
    assert out["files_materialized"] > 0
    assert out["bytes_read"] > 0
    assert out["receipt"]
    receipt = json.loads(Path(out["receipt"]).read_text(encoding="utf-8"))
    assert receipt["target"] == ids["app"]
    assert receipt["scope"] == "direct"
    assert receipt["workspace_id"]
    assert receipt["project_id"] == ids["app"]
    assert receipt["projects_selected"] == out["projects_selected"]


def test_no_workspace_refuses(tmp_path: Path) -> None:
    with pytest.raises(PortableError) as exc:
        context_resolve(tmp_path, scope="all")
    assert exc.value.kind == "workspace_not_found"


def test_unknown_scope_and_target_refuse(tmp_path: Path) -> None:
    ids = _make(tmp_path)
    with pytest.raises(PortableError) as exc:
        context_resolve(Path(ids["ws"]), target=ids["app"], scope="universe")
    assert exc.value.kind == "config_invalid"
    with pytest.raises(PortableError) as exc:
        context_resolve(Path(ids["ws"]), target="sfa-deadbeef", scope="target")
    assert exc.value.kind == "workspace_not_found"


def test_dependency_cycle_refuses(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    ws_mod.workspace_init(ws)
    ws_mod.workspace_add(ws, str(a))
    ws_mod.workspace_add(ws, str(b))
    st = ws_mod.workspace_status(ws)
    ids = {Path(p["resolved_path"]).name: p["id"] for p in st["projects"]}
    ws_mod.workspace_add(ws, str(a), depends_on=(ids["b"],))
    ws_mod.workspace_add(ws, str(b), depends_on=(ids["a"],))
    with pytest.raises(PortableError) as exc:
        context_resolve(ws, target=ids["a"], scope="transitive")
    assert exc.value.kind == "dependency_cycle"
