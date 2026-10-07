"""Surface lock (sections 87-88): CLI commands, MCP tools, schemas, capabilities.

    python scripts/check_surface_lock.py            # exit 1 on drift
    python scripts/check_surface_lock.py --update   # rewrite docs/surface.lock.json

Drift detected: tool added/removed, tool schema or risk changed (per-tool hash),
command added/removed, compact set changed, capability manifest changed.
Byte totals (inherited from the AWS lock) are recorded for economy tracking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "docs" / "surface.lock.json"
sys.path.insert(0, str(ROOT))


def _h(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def current() -> dict[str, Any]:
    from sparkforge_azure.cli.main import command_paths
    from sparkforge_azure.mcp.tools import load_all
    from sparkforge_azure.observability.surface import measure_surface

    tools = load_all()
    measured = measure_surface(ROOT)
    manifest = ROOT / "manifest.json"
    caps = json.loads(manifest.read_text(encoding="utf-8")).get("capabilities", []) \
        if manifest.is_file() else []
    return {
        "schema_version": 2,
        "basis": 'sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")))',
        "cli": {"commands": command_paths()},
        "mcp": {
            "tools": {n: {"schema_sha256": _h(s.declaration()), "risk": s.risk.to_dict(),
                          "compact": s.compact, "domain": s.domain}
                      for n, s in sorted(tools.items())},
            "tool_count": len(tools),
            "compact": sorted(n for n, s in tools.items() if s.compact),
            "total_bytes": measured["tools"]["total_bytes"],
            "compact_bytes": measured["compact"]["total_bytes"],
        },
        "capabilities": {"count": len(caps), "sha256": _h(caps)},
        "skills": {"count": measured["skills"]["document_count"],
                   "total_bytes": measured["skills"]["total_bytes"]},
        "knowledge": {"count": measured["knowledge"]["document_count"],
                      "total_bytes": measured["knowledge"]["total_bytes"]},
    }


def compare(lock_path: Path = LOCK) -> list[str]:
    if not lock_path.is_file():
        return ["surface lock missing"]
    old = json.loads(lock_path.read_text(encoding="utf-8"))
    new = current()
    drift: list[str] = []
    oc, nc = set(old["cli"]["commands"]), set(new["cli"]["commands"])
    drift += [f"command added: {c}" for c in sorted(nc - oc)]
    drift += [f"command removed: {c}" for c in sorted(oc - nc)]
    ot, nt = old["mcp"]["tools"], new["mcp"]["tools"]
    drift += [f"tool added: {t}" for t in sorted(set(nt) - set(ot))]
    drift += [f"tool removed: {t}" for t in sorted(set(ot) - set(nt))]
    for t in sorted(set(ot) & set(nt)):
        if ot[t]["schema_sha256"] != nt[t]["schema_sha256"]:
            drift.append(f"tool schema changed: {t}")
        if ot[t]["risk"] != nt[t]["risk"]:
            drift.append(f"tool risk changed: {t}")
    if old["mcp"]["compact"] != new["mcp"]["compact"]:
        drift.append("compact tool set changed")
    if old["capabilities"] != new["capabilities"]:
        drift.append("capability manifest changed")
    for k in ("skills", "knowledge"):
        if old.get(k, {}).get("count") != new[k]["count"]:
            drift.append(f"{k} count changed")
    return drift


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    args = ap.parse_args(argv)
    if args.update:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(current(), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "updated", "path": LOCK.relative_to(ROOT).as_posix()}))
        return 0
    drift = compare()
    print(json.dumps({"status": "ok" if not drift else "drift", "drift": drift}, indent=1))
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
