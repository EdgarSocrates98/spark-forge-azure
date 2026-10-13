"""Deterministic portability audit of a Spark Forge AWS checkout.

Produces the raw evidence behind ``docs/architecture/AWS_TO_AZURE_PORTABILITY_MATRIX.md``:
for every module of the AWS ``sparkforge`` package it records size, AWS-coupling
markers and intra-package dependencies.  The *classification* (COPY_SAFE, ADAPT,
REIMPLEMENT_AZURE_NATIVE, NOT_APPLICABLE, DEFER) is a human decision recorded in
``parity.yaml``; this script only supplies the evidence that decision must cite.

Usage::

    python scripts/aws_portability_audit.py <path-to-spark-forge-aws> \
        --out docs/architecture/evidence/aws_audit.json

The AWS checkout is never modified.  The output is sorted and timestamp-free so
two runs over the same SHA produce byte-identical JSON.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# Markers of AWS semantic coupling (§6 / §267 copy test).  Word-bounded so that
# e.g. "emr" inside "memory" does not count.
AWS_MARKERS = {
    "sdk": re.compile(r"\b(boto3|botocore)\b"),
    "arn": re.compile(r"arn:aws"),
    "glue": re.compile(r"\b(Glue|glue|GlueContext)\b"),
    "lakeformation": re.compile(r"(?i)lake_?formation"),
    "emr": re.compile(r"\b(EMR|emr)\b"),
    "s3": re.compile(r"\bS3\b|s3a?://"),
    "athena": re.compile(r"(?i)\bathena\b"),
    "cloudwatch": re.compile(r"(?i)\bcloudwatch\b"),
    "iam": re.compile(r"\bIAM\b"),
    "kinesis_msk": re.compile(r"(?i)\bkinesis\b|\bMSK\b"),
}


def _imports(tree: ast.AST, pkg: list[str]) -> tuple[set[str], set[str]]:
    internal: set[str] = set()
    external: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg[: len(pkg) - (node.level - 1)]
                names = [".".join(base + ([node.module] if node.module else []))]
            elif node.module:
                names = [node.module]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        for name in names:
            if name.startswith("sparkforge"):
                internal.add(name)
            elif name and name != "__future__":
                root = name.split(".")[0]
                if root not in sys.stdlib_module_names:
                    external.add(root)
    return internal, external


def audit(repo: Path) -> dict:
    pkg_root = repo / "sparkforge"
    if not pkg_root.is_dir():
        raise SystemExit(f"not a Spark Forge AWS checkout: {repo}")
    modules = []
    for path in sorted(pkg_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(repo).as_posix()
        parts = rel.split("/")
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        internal, external = _imports(tree, parts[:-1])
        own = rel[:-3].replace("/", ".")
        markers = {k: len(rx.findall(source)) for k, rx in AWS_MARKERS.items()}
        modules.append(
            {
                "module": own,
                "subsystem": parts[1] if len(parts) > 2 else parts[1][:-3],
                "loc": source.count("\n"),
                "aws_markers": {k: v for k, v in markers.items() if v},
                "aws_marker_total": sum(markers.values()),
                "imports_internal": sorted(i for i in internal if i != own),
                "imports_external": sorted(external),
            }
        )
    subsystems: dict[str, dict] = {}
    for mod in modules:
        sub = subsystems.setdefault(
            mod["subsystem"],
            {"files": 0, "loc": 0, "aws_marker_total": 0, "aws_files": 0, "depends_on": set()},
        )
        sub["files"] += 1
        sub["loc"] += mod["loc"]
        sub["aws_marker_total"] += mod["aws_marker_total"]
        sub["aws_files"] += 1 if mod["aws_marker_total"] else 0
        for dep in mod["imports_internal"]:
            seg = dep.split(".")
            if len(seg) > 1 and seg[1] != mod["subsystem"]:
                sub["depends_on"].add(seg[1])
    for sub in subsystems.values():
        sub["depends_on"] = sorted(sub["depends_on"])
    sha = ""
    try:
        sha = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", "-C", str(repo), "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "unknown"
    return {
        "schema_version": 1,
        "reference_repo": "EdgarSocrates98/spark-forge-aws",
        "reference_sha": sha,
        "marker_set": sorted(AWS_MARKERS),
        "totals": {
            "modules": len(modules),
            "loc": sum(m["loc"] for m in modules),
            "modules_with_aws_markers": sum(1 for m in modules if m["aws_marker_total"]),
        },
        "subsystems": dict(sorted(subsystems.items())),
        "modules": modules,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    report = audit(args.repo)
    text = json.dumps(report, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
