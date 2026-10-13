"""Wheel gate (sections 199-200, 184): reproducible build, multi-forge-safe contents, clean install.

1. Build the wheel twice into separate dirs with the same SOURCE_DATE_EPOCH;
   the sha256 must match (reproducible).
2. Every file in the wheel lives under ``sparkforge_azure/`` or ``*.dist-info/``;
   the only console script is ``sparkforge-azure`` (never ``sparkforge``).
3. Install the wheel into a brand-new venv (no repo on sys.path) and run
   ``sparkforge-azure version`` and ``doctor`` from outside the repository.

Prints one JSON document; exit 1 on any failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPOCH = "1580601600"


def _build(out: Path) -> Path:
    env = {**os.environ, "SOURCE_DATE_EPOCH": EPOCH}
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(out), "--quiet"], cwd=ROOT,
                   env=env, check=True)
    wheels = sorted(out.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected one wheel in {out}, got {wheels}")
    return wheels[0]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    problems: list[str] = []
    report: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="sfa-wheel-") as tmp:
        t = Path(tmp)
        w1, w2 = _build(t / "a"), _build(t / "b")
        report["wheel"] = w1.name
        report["sha256"] = _sha(w1)
        if _sha(w1) != _sha(w2):
            problems.append("wheel is not reproducible (two builds differ)")
        with zipfile.ZipFile(w1) as z:
            names = z.namelist()
            stray = [n for n in names if not (n.startswith("sparkforge_azure/")
                                              or ".dist-info/" in n)]
            if stray:
                problems.append(f"files outside sparkforge_azure/: {stray[:10]}")
            ep = next((n for n in names if n.endswith("entry_points.txt")), None)
            scripts = z.read(ep).decode() if ep else ""
            report["entry_points"] = scripts.strip().splitlines()
            for bad in ("sparkforge =", "sparkforge-tools ="):
                if bad in scripts:
                    problems.append(f"forbidden entrypoint {bad!r} (owned by spark-forge-aws)")
            for data in ("sparkforge_azure/_data/rules/catalog/",
                         "sparkforge_azure/_data/knowledge/",
                         "sparkforge_azure/_data/skills/"):
                if not any(n.startswith(data) for n in names):
                    problems.append(f"wheel lacks packaged data {data}")
        venv = t / "venv"
        subprocess.run(["uv", "venv", "--quiet", str(venv)], check=True)
        py = venv / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt"
                                                                  else "python")
        subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), str(w1)],
                       check=True)
        exe = py.parent / ("sparkforge-azure.exe" if os.name == "nt" else "sparkforge-azure")
        outside = t / "elsewhere"
        outside.mkdir()
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        for argv in ([str(exe), "version"], [str(exe), "doctor"]):
            proc = subprocess.run(argv, cwd=outside, capture_output=True, text=True, env=env,
                                  check=False)
            report[" ".join(argv[1:])] = proc.returncode
            if argv[1] == "version" and proc.returncode != 0:
                problems.append(f"clean install: version failed: {proc.stderr[-400:]}")
            if argv[1] == "doctor" and proc.returncode not in (0, 1):
                problems.append(f"clean install: doctor crashed: {proc.stderr[-400:]}")
        origin = subprocess.run([str(py), "-c", "import sparkforge_azure,sys;"
                                 "print(sparkforge_azure.__file__)"], cwd=outside,
                                capture_output=True, text=True, env=env, check=False).stdout
        if str(ROOT) in origin:
            problems.append("clean install imported the source tree, not the wheel")
        shutil.rmtree(venv, ignore_errors=True)
    report["status"] = "ok" if not problems else "fail"
    report["problems"] = problems
    sys.stdout.write(json.dumps(report, indent=1) + "\n")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
