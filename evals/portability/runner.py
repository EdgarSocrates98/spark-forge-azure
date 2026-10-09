"""Portability matrix runner (prompt_evo_portable.md §96–§101, §199).

Executa os casos de `suite.yaml` em temp dirs via a API
`sparkforge_azure.distribution` — nada de checkout paths, nada de HOME
real (§99–§100: HOME e XDG_CACHE_HOME apontam para o temp root; qualquer
escrita lá dentro reprova o caso `no_global_pollution`).

Cada caso é uma função `case_<id>` que monta a cena e devolve um dict de
observações; o runner compara com `expect:` do yaml. Sem pytest — é gate,
não teste unitário (os mesmos comportamentos já têm cobertura em
`tests/`; aqui a prova é *integração do ciclo inteiro* por cenário).

Uso::

    python evals/portability/runner.py [--json] [--case <id>]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sparkforge_azure.distribution import detach as detach_svc  # noqa: E402
from sparkforge_azure.distribution import service  # noqa: E402
from sparkforge_azure.distribution import workspace as ws_svc  # noqa: E402
from sparkforge_azure.distribution.context import context_resolve  # noqa: E402
from sparkforge_azure.distribution.errors import PortableError  # noqa: E402
from sparkforge_azure.distribution.hosts import detect_hosts  # noqa: E402
from sparkforge_azure.distribution.managed import MARKER_BEGIN  # noqa: E402
from sparkforge_azure.distribution.manifests import (  # noqa: E402
    load_project_identity,
    load_workspace_manifest,
)

LAB = Path(__file__).resolve().parent
REPORTS = LAB / "reports"


def _seed_project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(exist_ok=True)
    (root / "src" / "main.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (root / "README.md").write_text(f"# {root.name}\n", encoding="utf-8")


def _project_id(root: Path) -> str:
    return load_project_identity(root / ".sparkforge-azure" / "project.yaml").project_id


def _ws(root: Path):
    return load_workspace_manifest(root / ".sparkforge-azure" / "workspace.yaml")


# ---------------------------------------------------------------- cases

def case_single_repo(t: Path) -> dict[str, Any]:
    proj = t / "solo"
    _seed_project(proj)
    init = service.initialize(proj)
    status = service.status(proj)
    doc = service.doctor(proj)
    detach_svc.detach(proj)
    again = service.initialize(proj)
    return {
        "project_id_prefix": init["project_id"][:4],
        "status_ok": status["status"] == "ok" and doc["status"] == "ok",
        "detach_preserves_state": (proj / ".sparkforge-azure" / "project.yaml").is_file(),
        "reattach_same_id": again["project_id"] == init["project_id"],
    }


def case_monorepo(t: Path) -> dict[str, Any]:
    ws = t / "mono"
    (ws / "app").mkdir(parents=True)
    (ws / "lib").mkdir()
    ws_svc.workspace_init(ws)
    ws_svc.workspace_add(ws, "app")
    ws_svc.workspace_add(ws, "lib")
    decl = _ws(ws)
    rel = [p.path for p in decl.projects]
    return {
        "projects": len(decl.projects),
        "paths_relative": all(not Path(p).is_absolute() for p in rel),
        "workspace_id_prefix": decl.workspace_id[:4],
    }


def case_multi_repo(t: Path) -> dict[str, Any]:
    ws = t / "org" / "main"
    ext = t / "org" / "shared-lib"
    _seed_project(ws)
    _seed_project(ext)
    ws_svc.workspace_init(ws)
    ws_svc.workspace_add(ws, str(ext))
    decl = _ws(ws)
    external = [p for p in decl.projects if Path(p.path).is_absolute()]
    return {
        "external_marked": bool(external),
        "external_paths_absolute": all(Path(p.path).is_absolute() for p in external),
        "projects": len(decl.projects),
    }


def case_relocated_repo(t: Path) -> dict[str, Any]:
    ws = t / "ws"
    app = ws / "app"
    _seed_project(app)
    ws_svc.workspace_init(ws)
    ws_svc.workspace_add(ws, "app")
    before = _project_id(app)
    moved = ws / "moved" / "app"
    moved.parent.mkdir()
    app.rename(moved)
    add = ws_svc.workspace_add(ws, "moved/app")
    return {
        "id_survives_move": _project_id(moved) == before,
        "redeclared": add.get("action") == "relocated" or add["status"] == "ok",
        "add_outcome": add.get("action") or add["status"],
    }


def case_copied_repo(t: Path) -> dict[str, Any]:
    import shutil

    ws = t / "ws"
    app = ws / "app"
    _seed_project(app)
    service.initialize(app)
    ws_svc.workspace_init(ws)
    ws_svc.workspace_add(ws, "app")
    clone = ws / "app-copy"
    shutil.copytree(app, clone)
    try:
        ws_svc.workspace_add(ws, "app-copy")
        collision = None
    except PortableError as exc:
        collision = exc.kind
    regen = service.initialize(clone, regen_id=True)
    ws_svc.workspace_add(ws, "app-copy")
    return {
        "copy_needs_regen": collision == "identity_collision",
        "regen_new_id": regen["project_id"] != _project_id(app),
        "added_after_regen": any(p.id == regen["project_id"] for p in _ws(ws).projects),
    }


def _deps_workspace(t: Path) -> Path:
    """app -> lib -> base, arestas por id (o schema só aceita ids)."""
    ws = t / "ws"
    for name in ("app", "lib", "base"):
        _seed_project(ws / name)
    ws_svc.workspace_init(ws)
    ids = {}
    for name in ("app", "lib", "base"):
        out = ws_svc.workspace_add(ws, name)
        ids[name] = out["project"]["id"]
    ws_svc.workspace_add(ws, "app", depends_on=(ids["lib"],))
    ws_svc.workspace_add(ws, "lib", depends_on=(ids["base"],))
    return ws


def _selected_names(out: dict[str, Any]) -> set[str]:
    return {Path(str(p["root"])).name for p in out.get("projects", [])}


def case_direct_deps(t: Path) -> dict[str, Any]:
    ws = _deps_workspace(t)
    out = context_resolve(ws, target=str(ws / "app"), scope="direct")
    sel = _selected_names(out)
    return {
        "scope": "direct",
        "selected": sorted(sel),
        "target_in": "app" in sel,
        "direct_in": "lib" in sel,
        "excludes_transitive": "base" not in sel,
    }


def case_transitive_deps(t: Path) -> dict[str, Any]:
    ws = _deps_workspace(t)
    out = context_resolve(ws, target=str(ws / "app"), scope="transitive")
    sel = _selected_names(out)
    app_id = _project_id(ws / "app")
    ws_svc.workspace_add(ws, "base", depends_on=(app_id,))  # fecha o ciclo
    cycle_kind = None
    try:
        context_resolve(ws, target=str(ws / "app"), scope="transitive")
    except PortableError as exc:
        cycle_kind = exc.kind
    return {
        "scope": "transitive",
        "reaches_closure": {"app", "lib", "base"} <= sel,
        "cycle_refused": cycle_kind == "dependency_cycle",
        "cycle_kind": cycle_kind,
    }


def case_host_unavailable(t: Path) -> dict[str, Any]:
    hosts = detect_hosts(env_path=str(t / "empty-bin"))
    statuses = {h["status"] for h in hosts}
    proj = t / "proj"
    _seed_project(proj)
    init = service.initialize(proj)  # não pode falhar por host ausente
    return {
        "never_fails": init["status"] == "ok",
        "statuses": sorted(statuses),
        "no_unexpected": statuses <= {"available", "unavailable", "unproven",
                                      "unsupported"},
    }


def case_mcp_only(t: Path) -> dict[str, Any]:
    proj = t / "proj"
    _seed_project(proj)
    out = service.initialize(proj)  # sem --with-mirrors
    mcp = json.loads((proj / ".mcp.json").read_text(encoding="utf-8"))
    return {
        "mirrors_written": out["host_files"]["mirrors"]["written"],
        "mcp_key": "sparkforge-azure" in mcp["mcpServers"],
        "no_claude_dir": not (proj / ".claude").exists(),
        "marker_block": MARKER_BEGIN in (proj / "AGENTS.md").read_text(
            encoding="utf-8"),
    }


def case_detach_reattach(t: Path) -> dict[str, Any]:
    proj = t / "proj"
    _seed_project(proj)
    (proj / "AGENTS.md").write_text("# user rules\nkeep me\n", encoding="utf-8")
    first = service.initialize(proj, with_mirrors=True)
    detach_svc.detach(proj)
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    again = service.initialize(proj)
    return {
        "user_content_preserved": "keep me" in text and MARKER_BEGIN not in text,
        "mirrors_gone": not any((proj / ".claude").rglob("*.md"))
        if (proj / ".claude").exists() else True,
        "same_id_after_reattach": again["project_id"] == first["project_id"],
    }


CASES = {
    "single-repo": case_single_repo,
    "monorepo": case_monorepo,
    "multi-repo": case_multi_repo,
    "relocated-repo": case_relocated_repo,
    "copied-repo": case_copied_repo,
    "direct-deps": case_direct_deps,
    "transitive-deps": case_transitive_deps,
    "host-unavailable": case_host_unavailable,
    "mcp-only": case_mcp_only,
    "detach-reattach": case_detach_reattach,
}


# ------------------------------------------------------------- checking

def _check(case_id: str, expect: dict[str, Any], obs: dict[str, Any]) -> list[str]:
    """Contrato yaml ↔ observação. `expect` é a fonte; obs só é lida."""
    fails: list[str] = []
    for key, want in expect.items():
        got = obs.get(key)
        if key == "project_id_prefix":
            ok = str(obs.get("project_id_prefix", "")) == want
        elif key in {"projects", "mirrors_written"}:
            ok = got == want
        elif key == "statuses_allowed":
            ok = set(obs.get("statuses", ())) <= set(want)
        else:
            ok = bool(got) == bool(want)
        if not ok:
            fails.append(f"{case_id}: {key} expected {want!r}, got {got!r}")
    return fails


def _run_isolated(case_id: str) -> tuple[dict[str, Any], list[str]]:
    """Roda o caso com HOME/XDG redirecionados (§99–§100) e devolve
    (observações, poluição)."""
    env_keys = ("HOME", "XDG_CACHE_HOME", "USERPROFILE", "APPDATA",
                "LOCALAPPDATA")
    saved = {k: os.environ.get(k) for k in env_keys}
    pollution: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"sf-port-{case_id}-") as td:
        t = Path(td)
        fake_home = t / "fake-home"
        fake_home.mkdir()
        for k in env_keys:
            os.environ[k] = str(fake_home)
        try:
            obs = CASES[case_id](t / "work")
        finally:
            for k in env_keys:
                if saved[k] is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = saved[k]  # type: ignore[assignment]
        # §100: nada pode ter escrito no HOME falso
        leftovers = [str(p) for p in fake_home.rglob("*") if p.name != ""]
        if leftovers:
            pollution = leftovers
    return obs, pollution


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--case", dest="only", default=None)
    args = ap.parse_args()

    suite = yaml.safe_load((LAB / "suite.yaml").read_text(encoding="utf-8"))
    cases = suite["cases"] if not args.only else [
        c for c in suite["cases"] if c["id"] == args.only
    ]
    report: dict[str, Any] = {"suite": "portability", "tier": suite["tier"],
                              "results": []}
    all_fails: list[str] = []
    for case in cases:
        cid = case["id"]
        if cid not in CASES:
            all_fails.append(f"{cid}: no runner")
            continue
        obs, pollution = _run_isolated(cid)
        fails = _check(cid, case.get("expect") or {}, obs)
        if suite.get("no_global_pollution") and pollution:
            fails.append(f"{cid}: wrote to HOME: {pollution}")
        report["results"].append(
            {"case": cid, "status": "ok" if not fails else "fail",
             "observed": obs, "failures": fails}
        )
        all_fails.extend(fails)
    report["status"] = "ok" if not all_fails else "fail"
    report["failed"] = len(all_fails)

    REPORTS.mkdir(exist_ok=True)
    # `--case` é prova pontual: escreve artefato próprio e nunca sobrescreve
    # a matriz rastreada (a matriz é evidência do run completo — um caso
    # isolado não a representa; polish: o gate de frescura lia 1/1 depois
    # de qualquer prova de claim).
    out = (
        REPORTS / "portability-matrix.json"
        if not args.only
        else REPORTS / f"case-{args.only}.json"
    )
    out.write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    if args.json:
        print(json.dumps(report, indent=1, ensure_ascii=False))
    else:
        for r in report["results"]:
            mark = "ok  " if r["status"] == "ok" else "FAIL"
            print(f"{mark} {r['case']}")
            for f in r["failures"]:
                print(f"      {f}")
        print(f"portability: {report['status']} ({len(report['results'])} cases)")
    return 0 if not all_fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
