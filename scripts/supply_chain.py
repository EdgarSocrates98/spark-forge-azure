"""Supply chain (sections 195-201): hashed lock, lock verification, SBOM, offline audit.

    python scripts/supply_chain.py lock          # regenerate locks/*.lock with hashes (uv)
    python scripts/supply_chain.py verify-lock   # every pin exact + hashed + covers pyproject
    python scripts/supply_chain.py sbom --out sbom.cdx.json   # CycloneDX from the lock
    python scripts/supply_chain.py audit         # offline: lock vs locks/advisories.yaml floors

Offline by default.  The online advisory scan (pip-audit) is optional and lives
in CI; this script never touches the network except in ``lock`` (resolution).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

try:  # Python 3.11+; the 3.10 leg of the matrix skips lock tooling
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ROOT / "locks"
CORE_LOCK = LOCKS / "requirements.lock"
DEV_LOCK = LOCKS / "requirements-dev.lock"
ADVISORIES = LOCKS / "advisories.yaml"
_PIN = re.compile(r"^([A-Za-z0-9_.\-\[\]]+)==([^\s;\\]+)")


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.split("[")[0]).lower()


def parse_lock(path: Path) -> dict[str, dict]:
    """{name: {version, hashes}} from a pip-compile style lock with --hash lines."""
    out: dict[str, dict] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _PIN.match(line)
        if m:
            current = _norm(m.group(1))
            out[current] = {"version": m.group(2), "hashes": []}
        for h in re.findall(r"--hash=sha256:([0-9a-f]{64})", line):
            if current:
                out[current]["hashes"].append(h)
    return out


def cmd_lock(_: argparse.Namespace) -> int:
    LOCKS.mkdir(exist_ok=True)
    base = ["uv", "pip", "compile", "pyproject.toml", "--generate-hashes", "--universal",
            "--python-version", "3.10", "--quiet"]
    for extra, out in ((None, CORE_LOCK), ("dev", DEV_LOCK)):
        argv = [*base, "-o", out.relative_to(ROOT).as_posix()]
        if extra:
            argv += ["--extra", extra]
        proc = subprocess.run(argv, cwd=ROOT, check=False)
        if proc.returncode:
            return proc.returncode
    return 0


def _declared(extra: str | None) -> set[str]:
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    reqs = list(meta["dependencies"])
    if extra:
        reqs += meta["optional-dependencies"][extra]
    return {_norm(re.split(r"[<>=!~ ;]", r, maxsplit=1)[0]) for r in reqs}


def cmd_verify_lock(_: argparse.Namespace) -> int:
    problems: list[str] = []
    for path, extra in ((CORE_LOCK, None), (DEV_LOCK, "dev")):
        if not path.is_file():
            problems.append(f"missing {path.relative_to(ROOT)}")
            continue
        pins = parse_lock(path)
        for name, info in pins.items():
            if not info["hashes"]:
                problems.append(f"{path.name}: {name} has no --hash")
        for dep in _declared(extra):
            if dep not in pins:
                problems.append(f"{path.name}: declared dependency {dep} not in lock")
    print(json.dumps({"status": "ok" if not problems else "fail", "problems": problems},
                     indent=1))
    return 1 if problems else 0


def cmd_sbom(args: argparse.Namespace) -> int:
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pins = parse_lock(CORE_LOCK)
    components = [
        {
            "type": "library",
            "bom-ref": f"pkg:pypi/{n}@{i['version']}",
            "name": n,
            "version": i["version"],
            "purl": f"pkg:pypi/{n}@{i['version']}",
            "hashes": [{"alg": "SHA-256", "content": h} for h in sorted(i["hashes"])],
        }
        for n, i in sorted(pins.items())
    ]
    lock_digest = hashlib.sha256(CORE_LOCK.read_bytes()).hexdigest()
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{_uuid_from(lock_digest)}",
        "version": 1,
        "metadata": {
            "component": {"type": "application", "bom-ref": f"pkg:pypi/{meta['name']}",
                          "name": meta["name"], "version": meta["version"],
                          "purl": f"pkg:pypi/{meta['name']}@{meta['version']}"},
            "properties": [{"name": "sparkforge-azure:lock-sha256", "value": lock_digest}],
        },
        "components": components,
        "dependencies": [{"ref": f"pkg:pypi/{meta['name']}",
                          "dependsOn": [c["bom-ref"] for c in components]}],
    }
    text = json.dumps(bom, indent=1, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


def _uuid_from(digest: str) -> str:
    """Deterministic UUID (v5-shaped) from the lock digest: same lock -> same SBOM."""
    h = digest[:32]
    return f"{h[:8]}-{h[8:12]}-5{h[13:16]}-a{h[17:20]}-{h[20:32]}"


def _vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4])


def cmd_audit(_: argparse.Namespace) -> int:
    """Offline: every locked package at or above the curated security floor."""
    adv = yaml.safe_load(ADVISORIES.read_text(encoding="utf-8")) if ADVISORIES.is_file() else {}
    findings = []
    for path in (CORE_LOCK, DEV_LOCK):
        if not path.is_file():
            continue
        for name, info in parse_lock(path).items():
            for a in (adv or {}).get("advisories", []):
                if _norm(a["package"]) == name and _vtuple(info["version"]) < _vtuple(a["fixed"]):
                    findings.append({"lock": path.name, "package": name,
                                     "version": info["version"], "advisory": a["id"],
                                     "fixed": a["fixed"]})
    print(json.dumps({"status": "ok" if not findings else "fail", "findings": findings,
                      "basis": "offline curated floors (locks/advisories.yaml)"}, indent=1))
    return 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lock").set_defaults(func=cmd_lock)
    sub.add_parser("verify-lock").set_defaults(func=cmd_verify_lock)
    s = sub.add_parser("sbom")
    s.add_argument("--out")
    s.set_defaults(func=cmd_sbom)
    sub.add_parser("audit").set_defaults(func=cmd_audit)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
