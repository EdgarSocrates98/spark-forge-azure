"""W1 — portable distribution layer (prompt_evo_portable.md §10–§19).

Covers the lifecycle floor: inspect/init/status/doctor/detach on a temp
project, config precedence with recorded sources, strict manifest
validation, env overrides, and the managed-ledger contract that makes
detach reversible. Wheel-only execution (§94) is exercised by the
portability evals, not here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from sparkforge_azure.distribution import detach as detach_service
from sparkforge_azure.distribution import service
from sparkforge_azure.distribution.config import parse_overrides, resolve_config
from sparkforge_azure.distribution.errors import PortableError
from sparkforge_azure.distribution.hosts import detect_hosts, mcp_entry
from sparkforge_azure.distribution.managed import load_ledger
from sparkforge_azure.distribution.manifests import (
    init_project_identity,
    load_project_identity,
    load_workspace_manifest,
)
from sparkforge_azure.distribution.paths import resolve_paths


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    root = tmp_path / "my-project"
    root.mkdir()
    return root


def test_inspect_uninitialized_is_ok(project: Path) -> None:
    out = service.inspect(project)
    assert out["status"] == "ok"
    assert out["project"] is None
    assert out["capabilities"]["portable_distribution"] is True
    assert out["assets"]["asset_count"] > 0


def test_existing_verbs_work_without_distribution_init(tmp_path: Path) -> None:
    # §125–§127: `distribution init` is opt-in — pre-existing CLI verbs must
    # still succeed in a repo with no .sparkforge-azure/project.yaml.
    from sparkforge_azure.cli.main import main

    assert main(["version"]) == 0
    assert not (tmp_path / ".sparkforge-azure" / "project.yaml").exists()


def test_init_writes_identity_and_mcp(project: Path) -> None:
    out = service.initialize(project)
    assert out["status"] == "ok"
    assert out["project_id"].startswith("sfa-")
    manifest = project / ".sparkforge-azure" / "project.yaml"
    assert manifest.is_file()
    mcp = json.loads((project / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["sparkforge-azure"] == mcp_entry()
    # the managed ledger records everything we wrote
    ledger = load_ledger(project / ".sparkforge-azure")
    assert len(ledger["files"]) >= 3


def test_init_is_idempotent(project: Path) -> None:
    first = service.initialize(project)
    second = service.initialize(project)
    assert second["project_id"] == first["project_id"]
    assert "project_id" in second["kept"]


def test_init_regen_id_mints_new_identity(project: Path) -> None:
    first = service.initialize(project)
    regen = service.initialize(project, regen_id=True)
    assert regen["project_id"] != first["project_id"]
    assert "project_id_regenerated" in regen["created"]


def test_init_inside_initialized_project_refuses(project: Path) -> None:
    service.initialize(project)
    nested = project / "sub" / "dir"
    nested.mkdir(parents=True)
    with pytest.raises(PortableError) as exc:
        service.initialize(nested)
    assert exc.value.kind == "path_outside_root"


def test_status_uninitialized(tmp_path: Path) -> None:
    out = service.status(tmp_path / "empty")
    assert out["status"] == "uninitialized"


def test_status_detects_drift(project: Path) -> None:
    service.initialize(project)
    (project / ".mcp.json").unlink()
    out = service.status(project)
    assert out["status"] == "partial"
    assert any(d["state"] == "missing" for d in out["drift"])


def test_status_detects_modified(project: Path) -> None:
    service.initialize(project)
    mcp = project / ".mcp.json"
    mcp.write_text(
        json.dumps({"mcpServers": {"sparkforge-azure": {"command": "other"}}}),
        encoding="utf-8",
    )
    out = service.status(project)
    assert out["status"] == "drifted"


def test_status_broken_manifest(project: Path) -> None:
    service.initialize(project)
    (project / ".sparkforge-azure" / "project.yaml").write_text(
        "version: 1\nproject_id: nope\n", encoding="utf-8"
    )
    out = service.status(project)
    assert out["status"] == "broken"
    assert out["manifest_errors"]


def test_detach_preserves_state_and_reattaches(project: Path) -> None:
    first = service.initialize(project)
    out = detach_service.detach(project)
    assert out["status"] == "ok"
    assert not (project / ".mcp.json").exists()
    assert (project / ".sparkforge-azure" / "project.yaml").is_file()
    again = service.initialize(project)
    assert again["project_id"] == first["project_id"]


def test_detach_purge_state(project: Path) -> None:
    service.initialize(project)
    out = detach_service.detach(project, purge_state=True)
    assert out["state_preserved"] is False
    assert not (project / ".sparkforge-azure").exists()


def test_detach_dry_run_writes_nothing(project: Path) -> None:
    service.initialize(project)
    out = detach_service.detach(project, dry_run=True)
    assert out["dry_run"] is True
    assert (project / ".mcp.json").is_file()


def test_detach_preserves_user_owned_mcp_key(project: Path) -> None:
    mcp = project / ".mcp.json"
    mcp.write_text(
        json.dumps({"mcpServers": {"other-server": {"command": "x"},
                                   "sparkforge-azure": {"command": "user-owned"}}}),
        encoding="utf-8",
    )
    out = service.initialize(project)
    assert any("unmanaged" in w for w in out["warnings"])
    data = json.loads(mcp.read_text(encoding="utf-8"))
    assert data["mcpServers"]["sparkforge-azure"]["command"] == "user-owned"
    assert data["mcpServers"]["other-server"]["command"] == "x"


def test_detach_cache_preserved_by_default_purged_on_flag(project: Path) -> None:
    service.initialize(project)
    cache = project / ".sparkforge-azure" / "cache"
    cache.mkdir(parents=True)
    (cache / "blob.bin").write_bytes(b"cached")
    out = detach_service.detach(project)
    assert out["state_preserved"] is True
    assert (cache / "blob.bin").is_file()
    out = detach_service.detach(project, purge_cache=True)
    assert not cache.exists()
    # state itself still preserved — purge_cache ≠ purge_state
    assert (project / ".sparkforge-azure" / "project.yaml").is_file()


def test_detach_missing_asset_is_absent_not_error(project: Path) -> None:
    service.initialize(project)
    (project / ".mcp.json").unlink()  # user deleted it before detach
    out = detach_service.detach(project)
    states = {d["state"] for d in out["detached"]}
    assert "missing" in states
    assert out["status"] == "ok"


def test_detach_dry_run_purge_lists_but_keeps(project: Path) -> None:
    service.initialize(project)
    cache = project / ".sparkforge-azure" / "cache"
    cache.mkdir()
    out = detach_service.detach(project, dry_run=True, purge_state=True, purge_cache=True)
    assert any(p.startswith("would_remove:") for p in out["purged"])
    assert cache.is_dir() and (project / ".sparkforge-azure" / "project.yaml").is_file()


def test_user_config_and_set_refuse_secret_keys(tmp_path: Path) -> None:
    from sparkforge_azure.distribution.config import parse_overrides as po
    from sparkforge_azure.distribution.config import resolve_config as rc

    cfg = tmp_path / "user.yaml"
    cfg.write_text("connection_string: 'Server=x;Password=y'\n", encoding="utf-8")
    with pytest.raises(PortableError) as exc:
        rc(user_config_path=cfg)
    assert exc.value.kind == "config_invalid"
    with pytest.raises(PortableError):
        po(["network.token=abc"])
    # env-var references are legal — key name is the signal, not the value
    out = rc(cli_overrides={"network": {"mode": "env:SPARKFORGE_AZURE_NET"}})
    assert out["config"]["network"]["mode"] == "env:SPARKFORGE_AZURE_NET"


def test_manifest_refuses_secret_like_keys(project: Path) -> None:
    init_project_identity(project)
    manifest = project / ".sparkforge-azure" / "project.yaml"
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["config"] = {"client_secret": "abc"}
    manifest.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(PortableError) as exc:
        load_project_identity(manifest)
    assert exc.value.kind == "manifest_invalid"


def test_manifest_refuses_unknown_keys(project: Path) -> None:
    init_project_identity(project)
    manifest = project / ".sparkforge-azure" / "project.yaml"
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["rogue"] = True
    manifest.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(PortableError):
        load_project_identity(manifest)


def test_config_precedence_and_sources(tmp_path: Path) -> None:
    user = tmp_path / "user.yaml"
    user.write_text(
        yaml.safe_dump({"context": {"default_scope": "all"}, "network": {"mode": "live"}}),
        encoding="utf-8",
    )
    out = resolve_config(
        user_config_path=user,
        workspace_config={"context": {"default_scope": "transitive"}},
        project_config={"context": {"default_scope": "direct"}},
        cli_overrides={"context": {"default_scope": "target"}},
    )
    assert out["config"]["context"]["default_scope"] == "target"
    assert out["sources"]["context.default_scope"] == "cli"
    assert out["sources"]["network.mode"] == "user"
    assert out["sources"]["context.profile"] == "defaults"


def test_config_unknown_key_strict_and_lenient() -> None:
    with pytest.raises(PortableError) as exc:
        resolve_config(project_config={"bogus": {"key": 1}})
    assert exc.value.kind == "config_invalid"
    out = resolve_config(project_config={"bogus": {"key": 1}}, strict=False)
    assert "bogus.key" in out["unknown_keys"]


def test_parse_overrides() -> None:
    out = parse_overrides(["context.default_scope=direct", "x.y=1"])
    assert out == {"context": {"default_scope": "direct"}, "x": {"y": "1"}}
    with pytest.raises(PortableError):
        parse_overrides(["no-equals"])


def test_state_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom = tmp_path / "custom-state"
    monkeypatch.setenv("SPARKFORGE_AZURE_STATE_DIR", str(custom))
    paths = resolve_paths(cwd=tmp_path)
    assert paths.state_root == custom
    assert dict(paths.sources)["state_root"] == "environment"


def test_cache_env_override_and_switch(tmp_path: Path) -> None:
    paths = resolve_paths(
        cwd=tmp_path, env={"SPARKFORGE_AZURE_CACHE": str(tmp_path / "c")}
    )
    assert paths.cache_root == tmp_path / "c"
    switched = resolve_paths(cwd=tmp_path, env={"SPARKFORGE_AZURE_CACHE": "off"})
    assert switched.cache_root != tmp_path / "c"


def test_detect_hosts_never_fails_on_absence() -> None:
    hosts = detect_hosts(env_path="/nonexistent-path-dir")
    assert all(h["status"] in {"unavailable", "unproven"} for h in hosts)


def test_doctor_offline_and_uninitialized(tmp_path: Path) -> None:
    out = service.doctor(tmp_path / "bare")
    assert out["offline"] is True
    assert out["azure_auth_required"] is False
    assert all(c["status"] != "fail" for c in out["checks"])


def test_workspace_manifest_rejects_cycle_and_unknown_dep(
    tmp_path: Path,
) -> None:
    from sparkforge_azure.distribution.manifests import (
        ProjectDecl,
        WorkspaceDecl,
        write_workspace_manifest,
    )

    root = tmp_path / "ws"
    root.mkdir()
    decl = WorkspaceDecl(
        workspace_id="sfw-" + "0" * 24,
        name="ws",
        projects=(
            ProjectDecl(id="a", path="a", dependencies=("b",)),
            ProjectDecl(id="b", path="b", dependencies=("missing",)),
        ),
    )
    write_workspace_manifest(root, decl)
    with pytest.raises(PortableError) as exc:
        load_workspace_manifest(root / ".sparkforge-azure" / "workspace.yaml")
    assert exc.value.kind == "manifest_invalid"


def test_inspect_does_not_touch_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / "fake-home").mkdir()
    service.inspect(tmp_path)
    assert not list((tmp_path / "fake-home").iterdir())
