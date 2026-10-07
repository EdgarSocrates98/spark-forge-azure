"""Claims lock (sections 85-86, 222-224).

Every public claim in docs lives in ``docs/claims.lock.json`` with:
``id``, ``doc``, ``text`` (verbatim fragment that must appear in ``doc``),
``proof.cmd`` (argv list, run without a shell), ``proof.expect``
(``{"kind": "exit0"}`` | ``{"kind": "json", "path": "a.b", "op": "==|>=|in", "value": ...}``
| ``{"kind": "regex", "pattern": ...}``) and ``sha`` -- the commit the claim was proven at,
which must be an ancestor of HEAD.

    python scripts/check_claims.py            # verify all claims (runs proofs)
    python scripts/check_claims.py --static   # text + SHA only, no proof execution
    python scripts/check_claims.py --stamp    # re-run proofs and set sha=HEAD on success

Wording rules enforced (section 223/45/222): docs listed in claims may not say
"secure" about the product, nor state a savings percentage without a baseline claim.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "docs" / "claims.lock.json"
FORBIDDEN = [
    (re.compile(r"\b(is|são|é|totally|fully)\s+secure\b", re.I),
     'say "declared threat cases passed", not "secure"'),
    (re.compile(r"\b\d{1,3}\s?%\s+(token\s+)?(savings|economia|redu[cç][aã]o)", re.I),
     "savings percentage requires a same-case baseline claim"),
]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          check=False)


def _get(obj: Any, path: str) -> Any:
    for part in path.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def _expect(expect: dict[str, Any], proc: subprocess.CompletedProcess[str]) -> str | None:
    kind = expect.get("kind")
    if kind == "exit0":
        return None if proc.returncode == 0 else f"exit {proc.returncode}"
    if kind == "regex":
        return None if re.search(expect["pattern"], proc.stdout) else "pattern not found"
    if kind == "json":
        try:
            val = _get(json.loads(proc.stdout), expect["path"])
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            return f"json path {expect['path']}: {exc}"
        op, want = expect.get("op", "=="), expect["value"]
        ok = {"==": val == want, ">=": isinstance(val, (int, float)) and val >= want,
              "in": want in val if isinstance(val, (list, str, dict)) else False}.get(op)
        return None if ok else f"{expect['path']}={val!r} not {op} {want!r}"
    return f"unknown expect kind {kind!r}"


def verify(static: bool = False) -> list[dict[str, Any]]:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    results = []
    docs_checked: set[str] = set()
    for c in data["claims"]:
        problems: list[str] = []
        doc = ROOT / c["doc"]
        text = doc.read_text(encoding="utf-8") if doc.is_file() else ""
        if not text:
            problems.append(f"doc missing: {c['doc']}")
        elif c["text"] not in text:
            problems.append("claim text not found in doc (doc drifted from lock)")
        if c["doc"] not in docs_checked and text:
            docs_checked.add(c["doc"])
            for rx, why in FORBIDDEN:
                if rx.search(text):
                    problems.append(f"forbidden wording in {c['doc']}: {why}")
        sha = c.get("sha", "")
        if not sha or _git("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
            problems.append(f"sha {sha[:12] or '<none>'} is not an ancestor of HEAD")
        if not static:
            proc = subprocess.run([sys.executable if a == "python" else a
                                   for a in c["proof"]["cmd"]], cwd=ROOT, capture_output=True,
                                  text=True, timeout=c["proof"].get("timeout", 600), check=False)
            err = _expect(c["proof"]["expect"], proc)
            if err:
                problems.append(f"proof failed: {err}")
        results.append({"id": c["id"], "ok": not problems, "problems": problems})
    return results


def stamp() -> int:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    head = _git("rev-parse", "HEAD").stdout.strip()
    failed = []
    for c in data["claims"]:
        proc = subprocess.run([sys.executable if a == "python" else a for a in c["proof"]["cmd"]],
                              cwd=ROOT, capture_output=True, text=True,
                              timeout=c["proof"].get("timeout", 600), check=False)
        err = _expect(c["proof"]["expect"], proc)
        if err:
            failed.append({"id": c["id"], "error": err})
        else:
            c["sha"] = head
    LOCK.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"stamped": head, "failed": failed}, indent=1))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--stamp", action="store_true")
    args = ap.parse_args(argv)
    if args.stamp:
        return stamp()
    res = verify(static=args.static)
    bad = [r for r in res if not r["ok"]]
    print(json.dumps({"status": "ok" if not bad else "fail", "claims": len(res), "failed": bad},
                     indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
