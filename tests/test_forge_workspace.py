"""W2 — ForgeWorkspace lifecycle (prompt_evo_portable.md §20–§36).

Covers: bounded offline discovery, idempotent init, deterministic add
(including external repos and monorepo children), declaration-only remove,
cycle detection as an explicit review state, and locality reachability
(target/direct/transitive) shared with the context wave.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sparkforge_azure.distribution import workspace as ws_mod
from sparkforge_azure.distribution.errors import PortableError


@pytest.fixture()
def monorepo(tmp_path: Path) -> Path:
    root = tmp_path / "mono"
    for child in ("app", "shared", "infra"):
        (root / child).mkdir(parents=True)
    return root


@pytest.fixture()
def multirepo(tmp_path: Path) -> tuple[Path, Path]:
    app = tmp_path / "repo-app"
    lib = tmp_path / "repo-lib"
    app.mkdir()
    lib.mkdir()
    return app, lib


def _pid(root: Path) -> str:
    return yaml.safe_load(
        (root / ".sparkforge-azure" / "project.yaml").read_text(encoding="utf-8")
    )["project_id"]


def test_init_registers_host_project(monorepo: Path) -> None:
    out = ws_mod.workspace_init(monorepo)
    assert out["status"] == "ok"
    assert out["workspace_id"].startswith("sfw-")
    assert out["project_initialized"] is True
    assert (monorepo / ".sparkforge-azure" / "workspace.yaml").is_file()


def test_init_idempotent(monorepo: Path) -> None:
    first = ws_mod.workspace_init(monorepo)
    second = ws_mod.workspace_init(monorepo)
    assert second["workspace_id"] == first["workspace_id"]
    assert "workspace_id" in second["kept"]


def test_add_monorepo_child_stores_relative(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    out = ws_mod.workspace_add(monorepo, "app", role="application")
    assert out["action"] == "added"
    assert out["external"] is False
    assert out["project"]["path"] == "app"
    assert out["initialized_target"] is True


def test_add_external_repo_stores_absolute(multirepo: tuple[Path, Path]) -> None:
    app, lib = multirepo
    ws_mod.workspace_init(app)
    out = ws_mod.workspace_add(app, str(lib), role="shared")
    assert out["external"] is True
    assert Path(out["resolved_path"]) == lib.resolve()
    assert Path(out["project"]["path"]).is_absolute()


def test_add_is_deterministic_and_idempotent(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    first = ws_mod.workspace_add(monorepo, "shared")
    second = ws_mod.workspace_add(monorepo, "shared")
    assert first["action"] == "added"
    assert second["action"] == "kept"
    assert second["project"]["id"] == first["project"]["id"]


def test_add_requires_workspace(tmp_path: Path) -> None:
    with pytest.raises(PortableError) as exc:
        ws_mod.workspace_add(tmp_path, ".")
    assert exc.value.kind == "workspace_not_found"


def test_add_refuses_duplicate_path_different_id(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    ws_mod.workspace_add(monorepo, "shared")
    # force a second identity into the same dir is impossible via add —
    # simulate by writing another project.yaml, then re-adding a *fresh* id
    pid = _pid(monorepo / "shared")
    with pytest.raises(PortableError) as exc:
        ws_mod.workspace_add(monorepo, "shared", project_id="sfa-other")
    assert exc.value.kind == "identity_collision"
    assert _pid(monorepo / "shared") == pid  # untouched


def test_remove_is_declaration_only(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    added = ws_mod.workspace_add(monorepo, "shared")
    out = ws_mod.workspace_remove(monorepo, added["project"]["id"])
    assert out["repository_deleted"] is False
    assert (monorepo / "shared").is_dir()
    status = ws_mod.workspace_status(monorepo)
    assert added["project"]["id"] not in [p["id"] for p in status["projects"]]


def test_remove_strips_inbound_edges(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    ws_mod.workspace_add(monorepo, "shared")
    shared = _pid(monorepo / "shared")
    ws_mod.workspace_add(monorepo, "app", depends_on=(shared,))
    out = ws_mod.workspace_remove(monorepo, shared)
    assert out["inbound_edges_removed"]
    status = ws_mod.workspace_status(monorepo)
    app = next(p for p in status["projects"] if p["path"] == "app")
    assert app["dependencies"] == []


def test_status_reports_missing_project(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    ws_mod.workspace_add(monorepo, "infra")
    import shutil

    shutil.rmtree(monorepo / "infra")
    out = ws_mod.workspace_status(monorepo)
    assert out["status"] == "degraded"
    assert out["missing_projects"]


def test_cycle_is_explicit_review_state(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    ws_mod.workspace_add(monorepo, "app")
    ws_mod.workspace_add(monorepo, "shared")
    app, shared = _pid(monorepo / "app"), _pid(monorepo / "shared")
    ws_mod.workspace_add(monorepo, "app", depends_on=(shared,))
    out = ws_mod.workspace_add(monorepo, "shared", depends_on=(app,))
    assert out["status"] == "degraded"
    assert out["dependency_cycles"]
    status = ws_mod.workspace_status(monorepo)
    assert status["status"] == "dependency_cycle"
    with pytest.raises(PortableError) as exc:
        ws_mod.reachable(
            ws_mod.load_workspace_manifest(
                monorepo / ".sparkforge-azure" / "workspace.yaml"
            ),
            app,
            scope="transitive",
        )
    assert exc.value.kind == "dependency_cycle"


def test_reachability_scopes(monorepo: Path) -> None:
    ws_mod.workspace_init(monorepo)
    for name in ("app", "shared", "infra"):
        ws_mod.workspace_add(monorepo, name)
    app = _pid(monorepo / "app")
    shared = _pid(monorepo / "shared")
    infra = _pid(monorepo / "infra")
    host = _pid(monorepo)
    ws_mod.workspace_add(monorepo, "app", depends_on=(shared,))
    ws_mod.workspace_add(monorepo, "shared", depends_on=(infra,))
    ws = ws_mod.load_workspace_manifest(
        monorepo / ".sparkforge-azure" / "workspace.yaml"
    )
    assert ws_mod.reachable(ws, app, scope="target") == (app,)
    assert ws_mod.reachable(ws, app, scope="direct") == tuple(sorted({app, shared}))
    assert ws_mod.reachable(ws, app, scope="transitive") == tuple(
        sorted({app, shared, infra})
    )
    assert set(ws_mod.reachable(ws, app, scope="all")) == {
        app, shared, infra, host
    }


def test_discover_suggests_without_writing(monorepo: Path) -> None:
    (monorepo / "app" / "pyproject.toml").write_text("[project]\nname='app'\n")
    before = {p for p in monorepo.rglob("*")}
    out = ws_mod.workspace_discover(monorepo)
    assert out["status"] == "ok"
    assert {p for p in monorepo.rglob("*")} == before  # nothing written
    after_init = ws_mod.workspace_init(monorepo)
    out = ws_mod.workspace_discover(monorepo)
    assert out["workspace"]["workspace_id"] == after_init["workspace_id"]
    candidate_paths = {c["path"] for c in out["candidates"]}
    assert str((monorepo / "app").resolve()) in candidate_paths


def test_workspace_roundtrip_survives_within_root_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Move the whole workspace dir → same ids, same resolution (§40)."""
    root = tmp_path / "a" / "ws"
    (root / "app").mkdir(parents=True)
    ws_mod.workspace_init(root)
    ws_mod.workspace_add(root, "app")
    app_id = _pid(root / "app")
    ws_id = ws_mod.workspace_status(root)["workspace_id"]

    moved = tmp_path / "b" / "ws"
    moved.parent.mkdir()
    (tmp_path / "a" / "ws").rename(moved)
    status = ws_mod.workspace_status(moved)
    assert status["workspace_id"] == ws_id
    app = next(p for p in status["projects"] if p["id"] == app_id)
    assert app["exists"] is True
    assert app["resolved_path"] == str((moved / "app").resolve())
