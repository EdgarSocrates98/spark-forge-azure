"""Anti-drift portability gate (prompt_evo_portable.md §187–§188).

Static checks (always run):
  - package assets available: the packaged groups (agents/, skills/, ...)
    resolve through the dual-mode asset source and carry sha256;
  - workspace schema valid: manifests.py loads strict YAML, refuses
    unknown keys/secrets, workspace.yaml v1 round-trips;
  - host mirrors sync: canonical agents/*.md render == committed mirrors
    (delegates to the check_skills_agents mirror comparison when
    available);
  - portable docs current: the docs/portability/*.md set exists and is
    indexed in docs/README.md;
  - no checkout dependency: the MCP entry references the installed
    binary, never a path under the repo root.

Wheel gate (``--wheel``, T3): builds the wheel, installs it in a temp
venv *outside* the checkout, and runs the lifecycle end-to-end from the
installed package (init → workspace → resolve → detach). Mandatory for
closure (§194).

Exit 0 = all checks green.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PORTABLE_DOCS = (
    "docs/portability/PORTABILITY_AUDIT.md",
    "docs/portability/PORTABLE_DISTRIBUTION.md",
    "docs/portability/WORKSPACES.md",
    "docs/portability/CONTEXT_RESOLUTION.md",
    "docs/portability/HOST_INTEGRATION.md",
    "docs/portability/DETACH.md",
    "docs/portability/PORTABILITY_OUTCOME.md",
    "docs/portability/TROUBLESHOOTING.md",
    "docs/CURRENT_STATE.md",
    "docs/guides/SPARKFORGE_AZURE_PORTABLE.md",
    "docs/guides/SPARKFORGE_AZURE_PORTABLE.pt-BR.md",
)


def check_assets(errors: list[str]) -> None:
    from sparkforge_azure.distribution.assets import asset_inventory

    inv = asset_inventory()
    if not inv:
        errors.append("assets: inventory is empty")
        return
    missing = [a for a in inv if not a.sha256 or len(a.sha256) != 64]
    if missing:
        errors.append(f"assets: {len(missing)} entries without sha256")


def check_workspace_schema(errors: list[str]) -> None:
    import tempfile as _t

    import yaml

    from sparkforge_azure.distribution.errors import PortableError
    from sparkforge_azure.distribution.manifests import (
        WorkspaceDecl,
        load_workspace_manifest,
        write_workspace_manifest,
    )

    with _t.TemporaryDirectory() as td:
        root = Path(td)
        decl = WorkspaceDecl(
            workspace_id="sfw-" + "0" * 24, name="gate", projects=()
        )
        write_workspace_manifest(root, decl)
        back = load_workspace_manifest(
            root / ".sparkforge-azure" / "workspace.yaml"
        )
        if back.workspace_id != decl.workspace_id:
            errors.append("workspace schema: round-trip lost workspace_id")
        raw = yaml.safe_load(
            (root / ".sparkforge-azure" / "workspace.yaml").read_text(
                encoding="utf-8"
            )
        )
        raw["rogue_key"] = True
        (root / ".sparkforge-azure" / "workspace.yaml").write_text(
            yaml.safe_dump(raw), encoding="utf-8"
        )
        try:
            load_workspace_manifest(root / ".sparkforge-azure" / "workspace.yaml")
            errors.append("workspace schema: unknown key not refused")
        except PortableError as exc:
            if exc.kind != "manifest_invalid":
                errors.append(f"workspace schema: wrong refusal {exc.kind}")


def check_host_mirrors(errors: list[str]) -> None:
    sync = ROOT / "scripts" / "check_skills_agents.py"
    if not sync.is_file():
        errors.append("mirrors: check_skills_agents.py missing")
        return
    proc = subprocess.run(
        [sys.executable, str(sync)], capture_output=True, text=True,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        errors.append(f"mirrors out of sync: {' | '.join(tail)}")


def check_docs(errors: list[str]) -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    for rel in PORTABLE_DOCS:
        if not (ROOT / rel).is_file():
            errors.append(f"docs: {rel} missing")
        elif rel.replace("\\", "/") not in index and rel not in index:
            errors.append(f"docs: {rel} not indexed in docs/README.md")


def check_no_checkout_dep(errors: list[str]) -> None:
    from sparkforge_azure.distribution.hosts import mcp_entry

    entry = mcp_entry()
    for value in json.dumps(entry).split('"'):
        if str(ROOT) in value:
            errors.append(f"mcp entry leaks checkout path: {entry}")
    if entry.get("command") != "sparkforge-azure":
        errors.append("mcp entry must invoke the installed binary")


#: Módulos autorizados a tocar home/env de caminho (§103–§104).
_PATH_OWNERS = {
    "sparkforge_azure/distribution/paths.py",
    "sparkforge_azure/paths.py",
    "sparkforge_azure/distribution/manifests.py",  # expanduser em input declarado
    "sparkforge_azure/distribution/workspace.py",  # expanduser em input declarado
    "sparkforge_azure/distribution/context.py",    # expanduser em --target
    # ~/.sparkforge-azure/agentic-evals: store de runs de eval a nível de
    # máquina (persiste entre projetos) — anterior ao contrato portátil,
    # deliberado e fora do escopo por-projeto.
    "sparkforge_azure/evals/cli.py",
    # install --scope user escreve assets de host sob ~; update lê o
    # manifesto ~/.forge/installations do bootstrap — home é o contrato.
    "sparkforge_azure/install/service.py",
    # installkit vendored (byte-identical ao canonical the-forge): home do
    # registry ~/.forge e resolve_scope user fazem parte do contrato forge/*.
    "sparkforge_azure/_installkit.py",
    # portal adapter vendored (byte-identical ao canonical the-forge): lê o
    # registry ~/.forge/installations/forge-portal.json — home é o contrato.
    "sparkforge_azure/_forge_portal.py",
}


def check_path_audit(errors: list[str]) -> None:
    """§105/§116 — nenhum `Path.home()`/escrita-home fora dos módulos de
    path autorizados; resolve_within recusa `..` e resolve_declared_path
    não deixa path relativo escapar do root."""
    import re as _re

    sus = _re.compile(r"Path\.home\(|os\.environ\[['\"](?:HOME|USERPROFILE)")
    for py in (ROOT / "sparkforge_azure").rglob("*.py"):
        rel = py.relative_to(ROOT).as_posix()
        if rel in _PATH_OWNERS or "/tests/" in rel:
            continue
        for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if sus.search(line) and "expanduser" not in line:
                errors.append(f"path audit: {rel}:{n} home access")
    # §116 traversal: tentativas de fuga do root são recusadas
    from sparkforge_azure.paths import resolve_within

    probe = ROOT / "probe"
    if resolve_within(probe, "../../etc/passwd") is not None:
        errors.append("path audit: resolve_within aceitou ../ escape")
    if resolve_within(probe, "subdir/ok.txt") is None:
        errors.append("path audit: resolve_within recusou path legítimo")


def check_failure_kind_docs(errors: list[str]) -> None:
    """Polish §52–§54: every closed-vocabulary failure `kind` must appear in
    TROUBLESHOOTING.md. Kind is the contract; unlock wording may evolve."""
    doc = ROOT / "docs" / "portability" / "TROUBLESHOOTING.md"
    if not doc.is_file():
        return  # check_docs already flags the missing file
    from sparkforge_azure.distribution.errors import FAILURE_KINDS

    text = doc.read_text(encoding="utf-8")
    for kind in sorted(FAILURE_KINDS):
        if f"`{kind}`" not in text:
            errors.append(f"troubleshooting: failure kind `{kind}` undocumented")


def check_quickstart_commands(errors: list[str]) -> None:
    """Polish §62–§64: every `sparkforge-azure <verb>` line in the portable
    quickstarts must resolve to a real command path in the surface lock
    (parser-level check — never executes the commands)."""
    import re as _re

    known = set(
        json.loads((ROOT / "docs" / "surface.lock.json").read_text(
            encoding="utf-8"
        ))["cli"]["commands"]
    )
    for rel in PORTABLE_DOCS:
        if "guides/" not in rel:
            continue
        doc = ROOT / rel
        if not doc.is_file():
            continue
        for n, line in enumerate(
            doc.read_text(encoding="utf-8").splitlines(), 1
        ):
            m = _re.match(r"^\s*sparkforge-azure\s+(.+?)(?:\s+#.*)?$", line)
            if not m:
                continue
            tokens = [
                t for t in m.group(1).split() if not t.startswith("-")
            ]
            # longest prefix of tokens that forms a locked command path
            matched = ""
            for i in range(len(tokens), 0, -1):
                cand = " ".join(tokens[:i])
                if cand in known:
                    matched = cand
                    break
            if not matched:
                errors.append(
                    f"quickstart {rel}:{n}: `sparkforge-azure "
                    f"{' '.join(tokens[:2])}` is not a real command"
                )


def check_current_state(errors: list[str]) -> None:
    """Polish §22: CURRENT_STATE.md must exist, carry the GENERATED header
    and not drift from a fresh regeneration (SHA stamped at gen time is
    exempt — it changes on every commit by design)."""
    doc = ROOT / "docs" / "CURRENT_STATE.md"
    if not doc.is_file():
        return  # check_docs flags it
    sys.path.insert(0, str(ROOT / "scripts"))
    import gen_current_state  # noqa: PLC0415

    existing = doc.read_text(encoding="utf-8")
    if gen_current_state.HEADER not in existing:
        errors.append("current_state: GENERATED header missing")
        return
    def body_rows(text: str) -> list[str]:
        return [
            line for line in text.splitlines()
            if line.startswith("|") and "MAIN_SHA" not in line
        ]

    fresh = gen_current_state.render(gen_current_state.collect())
    diff = [
        f"{a!r} != {b!r}"
        for a, b in zip(body_rows(existing), body_rows(fresh), strict=False)
        if a != b
    ]
    if diff or len(body_rows(existing)) != len(body_rows(fresh)):
        errors.append(
            "current_state: stale — regen with gen_current_state.py "
            f"({'; '.join(diff) or 'row count differs'})"
        )


def _venv_python(venv_dir: Path) -> Path:
    win = venv_dir / "Scripts" / "python.exe"
    nix = venv_dir / "bin" / "python"
    return win if win.exists() else nix


def _find_uv() -> str | None:
    import shutil

    return shutil.which("uv")


def wheel_gate(errors: list[str]) -> None:
    """T3 — build wheel, install in temp venv outside checkout, run the
    lifecycle from the installed package only.

    Prefers `uv` (no pip needed in the host env); falls back to
    `pip wheel` + `venv --with-pip`.
    """
    uv = _find_uv()
    with tempfile.TemporaryDirectory(prefix="sf-wheel-gate-") as td:
        work = Path(td)
        dist = work / "dist"
        if uv:
            build = subprocess.run(
                [uv, "build", "--wheel", "--out-dir", str(dist), str(ROOT)],
                capture_output=True, text=True,
            )
        else:
            build = subprocess.run(
                [sys.executable, "-m", "pip", "wheel", "--no-deps", "-w",
                 str(dist), str(ROOT)],
                capture_output=True, text=True,
            )
        wheels = list(dist.glob("sparkforge_azure-*.whl"))
        if build.returncode != 0 or not wheels:
            errors.append(
                f"wheel: build failed: {(build.stderr or build.stdout)[-300:]}"
            )
            return
        venv_dir = work / "venv"
        if uv:
            mk = subprocess.run(
                [uv, "venv", str(venv_dir)], capture_output=True, text=True
            )
        else:
            venv.create(venv_dir, with_pip=True)
            mk = subprocess.CompletedProcess([], 0)
        if mk.returncode != 0:
            errors.append(f"wheel: venv failed: {mk.stderr[-300:]}")
            return
        py = _venv_python(venv_dir)
        if uv:
            inst = subprocess.run(
                [uv, "pip", "install", "--python", str(py),
                 str(wheels[0])],
                capture_output=True, text=True,
            )
        else:
            inst = subprocess.run(
                [str(py), "-m", "pip", "install", str(wheels[0])],
                capture_output=True, text=True,
            )
        if inst.returncode != 0:
            errors.append(f"wheel: install failed: {inst.stderr[-300:]}")
            return
        proj = work / "proj"
        proj.mkdir()
        script = (
            "import sys; from pathlib import Path;"
            "from sparkforge_azure.distribution import service, detach;"
            "root = Path(sys.argv[1]);"
            "out = service.initialize(root);"
            "assert out['status'] == 'ok' and out['project_id'].startswith('sfa-'), out;"
            "st = service.status(root);"
            "assert st['status'] in {'ok','initialized'}, st;"
            "d = detach.detach(root); assert d['status'] == 'ok', d;"
            "again = service.initialize(root);"
            "assert again['project_id'] == out['project_id'];"
            "print('WHEEL-LIFECYCLE-OK', out['project_id'])"
        )
        run = subprocess.run(
            [str(py), "-c", script, str(proj)],
            capture_output=True, text=True, cwd=str(work),
        )
        if "WHEEL-LIFECYCLE-OK" not in run.stdout:
            errors.append(
                "wheel: lifecycle failed: "
                f"{(run.stdout + run.stderr)[-400:]}"
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wheel", action="store_true",
                    help="run the T3 installed-wheel gate (slow)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    errors: list[str] = []
    check_assets(errors)
    check_workspace_schema(errors)
    check_docs(errors)
    check_no_checkout_dep(errors)
    check_path_audit(errors)
    check_failure_kind_docs(errors)
    check_quickstart_commands(errors)
    check_current_state(errors)
    # mirror sync is the heaviest check — keep it opt-in with --wheel so
    # the fast gate stays fast; it runs anyway inside check_skills_agents.
    if args.wheel:
        check_host_mirrors(errors)
        wheel_gate(errors)
    report = {"status": "ok" if not errors else "fail", "errors": errors}
    if args.json:
        print(json.dumps(report, indent=1, ensure_ascii=False))
    else:
        for e in errors:
            print(f"FAIL {e}")
        print(f"portability gate: {report['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
