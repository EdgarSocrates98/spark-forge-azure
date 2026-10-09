"""W3 — relocatable identity (prompt_evo_portable.md §37–§43, §64).

`project_id` is generated once and persisted — moving a project keeps the
identity (the manifest travels with the directory), while *copying* one is
an explicit `identity_collision` review state, never a silent merge.
State/cache/index namespaces key by logical id so two projects sharing an
overridden root never collide.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from sparkforge_azure.distribution import service
from sparkforge_azure.distribution import workspace as ws_mod
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.identity import (
    codeintel_db,
    project_cache_dir,
    project_state_dir,
    receipt_namespace,
)
from sparkforge_azure.distribution.paths import resolve_paths


def _pid(root: Path) -> str:
    return yaml.safe_load(
        (root / ".sparkforge-azure" / "project.yaml").read_text(encoding="utf-8")
    )["project_id"]


def test_project_id_survives_move(tmp_path: Path) -> None:
    a = tmp_path / "a" / "proj"
    a.mkdir(parents=True)
    first = service.initialize(a)
    b = tmp_path / "b" / "proj"
    b.parent.mkdir(parents=True)
    a.rename(b)
    out = service.status(b)
    assert out["project"]["project_id"] == first["project_id"]
    assert out["project"]["root"] == str(b.resolve())


def test_copy_is_identity_collision_not_merge(tmp_path: Path) -> None:
    ws_root = tmp_path / "ws"
    lib = tmp_path / "lib"
    copy = tmp_path / "lib-copy"
    ws_root.mkdir()
    lib.mkdir()
    ws_mod.workspace_init(ws_root)
    ws_mod.workspace_add(ws_root, str(lib))
    lib_id = _pid(lib)

    shutil.copytree(lib, copy)  # project.yaml comes along — same id
    with pytest.raises(PortableError) as exc:
        ws_mod.workspace_add(ws_root, str(copy))
    assert exc.value.kind == "identity_collision"
    # the declared entry still points at the original
    status = ws_mod.workspace_status(ws_root)
    entry = next(p for p in status["projects"] if p["id"] == lib_id)
    assert Path(entry["resolved_path"]) == lib.resolve()


def test_regen_id_makes_copy_addable(tmp_path: Path) -> None:
    ws_root = tmp_path / "ws"
    lib = tmp_path / "lib"
    copy = tmp_path / "lib-copy"
    ws_root.mkdir()
    lib.mkdir()
    ws_mod.workspace_init(ws_root)
    ws_mod.workspace_add(ws_root, str(lib))
    lib_id = _pid(lib)
    shutil.copytree(lib, copy)
    service.initialize(copy, regen_id=True)
    copy_id = _pid(copy)
    assert copy_id != lib_id
    out = ws_mod.workspace_add(ws_root, str(copy))
    assert out["action"] == "added"
    assert out["project"]["id"] == copy_id


def test_external_relocation_recorded_not_collided(tmp_path: Path) -> None:
    ws_root = tmp_path / "ws"
    lib = tmp_path / "lib"
    moved = tmp_path / "elsewhere" / "lib"
    ws_root.mkdir()
    lib.mkdir()
    ws_mod.workspace_init(ws_root)
    ws_mod.workspace_add(ws_root, str(lib))
    lib_id = _pid(lib)
    moved.parent.mkdir()
    lib.rename(moved)
    out = ws_mod.workspace_add(ws_root, str(moved))
    assert out["action"] == "relocated"
    assert out["project"]["id"] == lib_id


def test_state_namespace_isolation(tmp_path: Path) -> None:
    shared = tmp_path / "shared-state"
    paths_env = resolve_paths(
        cwd=tmp_path, env={"SPARKFORGE_AZURE_STATE_DIR": str(shared)}
    )
    a = project_state_dir(paths_env, "sfa-aaa")
    b = project_state_dir(paths_env, "sfa-bbb")
    assert a == shared / "projects" / "sfa-aaa"
    assert a != b
    # project-anchored default keeps the classic layout (back-compat)
    paths_local = resolve_paths(cwd=tmp_path, env={})
    assert project_state_dir(paths_local, "sfa-aaa") == paths_local.state_root


def test_cache_namespace_includes_workspace(tmp_path: Path) -> None:
    paths = resolve_paths(
        cwd=tmp_path, env={"SPARKFORGE_AZURE_CACHE": str(tmp_path / "c")}
    )
    out = project_cache_dir(paths, "sfa-a", workspace_id="sfw-w")
    assert out == tmp_path / "c" / "sfw-w" / "projects" / "sfa-a"


def test_codeintel_db_keyed_by_project(tmp_path: Path) -> None:
    paths = resolve_paths(
        cwd=tmp_path, env={"SPARKFORGE_AZURE_STATE_DIR": str(tmp_path / "s")}
    )
    db = codeintel_db(paths, "sfa-x")
    assert "sfa-x" in db.as_posix()
    assert db.name == "graph.sqlite3"


def test_receipt_namespace_tuple() -> None:
    ns = receipt_namespace("sfa-p", "sfw-w", scope="direct")
    assert ns == {
        "project_id": "sfa-p",
        "workspace_id": "sfw-w",
        "context_scope": "direct",
    }


def test_init_receipt_carries_workspace_id(tmp_path: Path) -> None:
    import json

    ws_root = tmp_path / "ws"
    ws_root.mkdir()
    ws = ws_mod.workspace_init(ws_root)
    # workspace init does not write the distribution receipt; init does
    service.initialize(ws_root)
    receipt = json.loads(
        (ws_root / ".sparkforge-azure" / "receipt-distribution.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["workspace_id"] == ws["workspace_id"]
