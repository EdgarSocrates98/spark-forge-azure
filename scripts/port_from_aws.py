"""Audited port of provider-neutral modules from a Spark Forge AWS checkout.

This is the ONLY sanctioned path for bringing AWS code into this repository
(portability matrix, section "Classes").  It enforces the copy test of the
foundational prompt (section 267) and records provenance.

Per entry in ``scripts/port_manifest.yaml``:

* ``COPY_SAFE`` -- refused if the source carries any AWS-coupling marker.  The
  ported bytes are locked in ``provenance.json``; editing the file later without
  reclassifying it as ``ADAPT`` fails ``tests/test_provenance.py``.
* ``ADAPT`` -- must list ``changes`` (what was/will be adapted).  The file is
  copied once; subsequent runs never overwrite it (manual adaptation wins).

Mechanical rewrites applied to every ported file -- and nothing else:

1. Python package ``sparkforge`` -> ``sparkforge_azure`` (ADR-0002).
2. Environment prefix ``SPARKFORGE_`` -> ``SPARKFORGE_AZURE_`` (multi-forge RFC).
3. State directory ``.sparkforge`` -> ``.sparkforge-azure`` (multi-forge RFC).

Domain terms (AWS -> Azure, Glue -> ADF, ...) are NEVER rewritten (section 269).

Usage::

    python scripts/port_from_aws.py <aws-checkout> [--only PREFIX] [--force-copy-safe]
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

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "port_manifest.yaml"
PROVENANCE = ROOT / "docs" / "architecture" / "evidence" / "provenance.json"

sys.path.insert(0, str(ROOT / "scripts"))
from aws_portability_audit import AWS_MARKERS  # noqa: E402

# Only import-shaped occurrences: `sparkforge.x`, `import sparkforge`, `from sparkforge import`.
# Prose such as "run `sparkforge analyze`" names the AWS CLI and is left for manual review.
_PKG = re.compile(r"\bsparkforge(?=\.\w)|(?<=import )sparkforge\b|(?<=from )sparkforge\b")
_PKG_STR = re.compile(r"(['\"])sparkforge(['\"/.])")
_ENV = re.compile(r"\bSPARKFORGE_(?!AZURE_)")
_STATE = re.compile(r"\.sparkforge(?![-_\w])")


def rewrite(text: str) -> str:
    text = _STATE.sub(".sparkforge-azure", text)
    text = _ENV.sub("SPARKFORGE_AZURE_", text)
    text = _PKG_STR.sub(lambda m: f"{m.group(1)}sparkforge_azure{m.group(2)}", text)
    return _PKG.sub("sparkforge_azure", text)


def markers(text: str) -> dict[str, int]:
    found = {k: len(rx.findall(text)) for k, rx in AWS_MARKERS.items()}
    return {k: v for k, v in found.items() if v}


def destination(src: str, entry: dict) -> str:
    if entry.get("dst"):
        return entry["dst"]
    if src.startswith("sparkforge/"):
        return "sparkforge_azure/" + src[len("sparkforge/") :]
    return src


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("aws_repo", type=Path)
    ap.add_argument("--only", default="", help="port only entries whose src starts with this")
    ap.add_argument("--force-copy-safe", action="store_true")
    args = ap.parse_args(argv)

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    sha = subprocess.run(  # noqa: S603
        ["git", "-C", str(args.aws_repo), "rev-parse", "HEAD"],  # noqa: S607
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if sha != manifest["reference_sha"]:
        print(f"refusing: AWS checkout at {sha}, manifest pins {manifest['reference_sha']}")
        return 2

    prov = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    prov.setdefault("schema_version", 1)
    prov["reference_repo"] = "EdgarSocrates98/spark-forge-aws"
    prov["reference_sha"] = sha
    files = prov.setdefault("files", {})
    errors: list[str] = []

    for entry in manifest["entries"]:
        src = entry["src"]
        if args.only and not src.startswith(args.only):
            continue
        klass = entry["class"]
        src_path = args.aws_repo / src
        raw = src_path.read_bytes()
        text = raw.decode("utf-8")
        found = markers(text)
        dst = destination(src, entry)
        dst_path = ROOT / dst
        if klass == "COPY_SAFE" and found:
            errors.append(f"{src}: COPY_SAFE but AWS markers {found}; classify ADAPT")
            continue
        if klass == "ADAPT" and not entry.get("changes"):
            errors.append(f"{src}: ADAPT requires 'changes'")
            continue
        if klass not in {"COPY_SAFE", "ADAPT"}:
            errors.append(f"{src}: unknown class {klass}")
            continue
        ported = rewrite(text)
        write = (
            not dst_path.exists()
            or (klass == "COPY_SAFE" and args.force_copy_safe)
        )
        if write:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_text(ported, encoding="utf-8", newline="\n")
        record = {
            "src": src,
            "class": klass,
            "source_sha256": _sha(raw),
            "aws_markers": found,
        }
        if klass == "COPY_SAFE":
            record["ported_sha256"] = _sha(ported.encode("utf-8"))
        else:
            record["changes"] = entry["changes"]
        files[dst] = record

    prov["files"] = dict(sorted(files.items()))
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.write_text(json.dumps(prov, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for err in errors:
        print("ERROR", err)
    print(f"ported entries recorded: {len(files)}; errors: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
